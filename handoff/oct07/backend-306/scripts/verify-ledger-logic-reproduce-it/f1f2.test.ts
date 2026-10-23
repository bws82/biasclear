// Independent reproduction of F1/F2 (offline; FakeAws + DynamoDB conflict rule; no network).
import { describe, expect, it } from "vitest";
import type { EvaluationResult } from "../../pr10b-wt/packages/explain/src/app.js";
import { Ddb } from "../../pr10b-wt/packages/explain/src/aws/dynamodb.js";
import { BILLING_PAUSE_KEY, persistBillingPause, reserve, settle, spendKeys } from "../../pr10b-wt/packages/explain/src/spend.js";
import { FakeAws, config, evalEvent, harness, lastLog, modelReply } from "../../pr10b-wt/packages/explain/test/helpers.js";
import { Locks, later, waitFor } from "./ddblock.js";

const cfg = config();

describe("F1 reproduce", () => {
  it("A's ordinary settle cancelled by B's in-progress reservation => durable no-TTL pause", async () => {
    const aws = new FakeAws();
    const L = new Locks(aws.transport);
    const A = harness({ transport: L.transport });
    const B = harness({ transport: L.transport });
    const modelGate = later();
    let n = 0;
    aws.model = async () => { n++; if (n === 1) await modelGate.p; return { status: 200, json: modelReply() }; };
    const pa = A.handler(evalEvent()) as Promise<EvaluationResult>;
    await waitFor(() => aws.modelCalls.length === 1);
    const bIn = later(); const bOut = later(); let armed = true;
    L.gate = (_p, k) => { if (armed && k === "reserve") { armed = false; bIn.go(); return bOut.p; } return undefined; };
    const pb = B.handler(evalEvent()) as Promise<EvaluationResult>;
    await bIn.p;                 // B's reservation is now in progress on pause/month/day/event
    // B's reservation commits right after A's settle is cancelled (env RELEASE_B=late keeps it held through A's persist)
    if (process.env.RELEASE_B !== "late") L.onConflict = (k) => { if (k === "settle") { bOut.go(); } };
    modelGate.go();              // A's model answers normally; A settles now
    await waitFor(() => L.log.some((l) => l.startsWith("CONFLICT settle")));
    if (process.env.RELEASE_B === "late") { await waitFor(() => A.logs.length === 1); bOut.go(); }
    const [a, b] = await Promise.all([pa, pb]);
    const la = lastLog(A), lb = lastLog(B);
    console.log("F1a log", L.log);
    console.log("F1a A", a.status, la.code, "actual", la.actualMicros, "reserved", la.reservedMicros, "pausePersisted", la.pausePersisted, "overrun", la.overrun);
    console.log("F1a B", b.status, lb.code);
    const pause = aws.table.items.get(BILLING_PAUSE_KEY);
    console.log("F1a pause item", pause);
    expect(la.code).toBe("E_SETTLE");
    expect(la.actualMicros as number).toBeLessThan(la.reservedMicros as number);
    expect(pause?.ttl).toBeUndefined();
    expect(pause).toBeDefined();
    // Fresh instance next month: still refused before any model call.
    const C = harness({ transport: L.transport });
    C.clock.ms = A.clock.ms + 40 * 86_400_000;
    const calls = aws.modelCalls.length;
    const c = (await C.handler(evalEvent())) as EvaluationResult;
    console.log("F1a fresh instance", new Date(C.clock.ms).toISOString(), c.status, lastLog(C).code);
    expect(lastLog(C).code).toBe("E_BILLING_PAUSE");
    expect(aws.modelCalls.length).toBe(calls);
    // Month counter: A's reservation retained (over-count), nothing lost.
    const k = spendKeys(A.clock.ms);
    console.log("F1a month m", aws.table.num(k.month, "m"), "A event state", aws.table.items.get(`billing#${String(la.event ?? "")}`));
  });

  it("A's settle cancelled by B's concurrent *settle* (two normal answers finishing together)", async () => {
    const aws = new FakeAws();
    const L = new Locks(aws.transport);
    const A = harness({ transport: L.transport });
    const B = harness({ transport: L.transport });
    const g = later();
    aws.model = async () => { await g.p; return { status: 200, json: modelReply() }; };
    const pa = A.handler(evalEvent()) as Promise<EvaluationResult>;
    await waitFor(() => aws.modelCalls.length === 1);
    const pb = B.handler(evalEvent()) as Promise<EvaluationResult>;
    await waitFor(() => aws.modelCalls.length === 2);
    const hold = later(); let armed = true;
    L.gate = (_p, k) => { if (armed && k === "settle") { armed = false; setTimeout(() => hold.go(), 5); return hold.p; } return undefined; };
    g.go();
    const [a, b] = await Promise.all([pa, pb]);
    console.log("F1b log", L.log, "A", a.status, lastLog(A).code, "B", b.status, lastLog(B).code, "pause?", aws.table.items.has(BILLING_PAUSE_KEY));
    expect([lastLog(A).code, lastLog(B).code]).toContain("E_SETTLE");
  });

  it("429 (not billed) + release conflict => durable pause with actual 0", async () => {
    const aws = new FakeAws();
    const L = new Locks(aws.transport);
    const A = harness({ transport: L.transport });
    // Another instance's transaction is in progress on the day key at the moment A releases.
    aws.model = () => { L.held.set(spendKeys(A.clock.ms).day, 1); return { status: 429, errorType: "ThrottlingException" }; };
    const r = (await A.handler(evalEvent())) as EvaluationResult;
    L.held.clear();
    console.log("F1c", r.status, lastLog(A).code, lastLog(A).actualMicros, lastLog(A).pausePersisted, L.log);
    expect(lastLog(A).code).toBe("E_SETTLE");
    expect(aws.table.items.has(BILLING_PAUSE_KEY)).toBe(true);
  });
});

describe("F2 reproduce", () => {
  it("two concurrent persistBillingPause calls: loser has no debt row", async () => {
    const aws = new FakeAws();
    const L = new Locks(aws.transport);
    const ddb = new Ddb(L.transport, cfg.region, cfg.table);
    const now = Date.UTC(2026, 9, 7, 14);
    const a = await reserve(ddb, cfg, now, 10_000); const b = await reserve(ddb, cfg, now, 10_000);
    if (!a.ok || !b.ok) throw new Error("no reservation");
    const h = later(); let armed = true;
    L.gate = (_p, k) => { if (armed && k === "persist") { armed = false; return h.p; } return undefined; };
    const p1 = persistBillingPause(ddb, { reason: "E_SETTLE", nowMs: now, reservedMicros: 10_000, actualMicros: 1_500_000, event: a.reservation.event });
    await waitFor(() => !armed);
    const r2 = await persistBillingPause(ddb, { reason: "E_SETTLE", nowMs: now, reservedMicros: 10_000, actualMicros: 1_600_000, event: b.reservation.event });
    h.go();
    const r1 = await p1;
    const debts = [...aws.table.items.keys()].filter((k) => k.startsWith("billingdebt#"));
    console.log("F2a", r1, r2, debts, "month", aws.table.num(a.reservation.month, "m"), L.log);
    expect(r2).toBe(false);
    expect(debts.length).toBe(1);
  });

  it("persistBillingPause vs an ordinary reservation from another instance (ConditionCheck on billing#pause)", async () => {
    const aws = new FakeAws();
    const L = new Locks(aws.transport);
    const ddb = new Ddb(L.transport, cfg.region, cfg.table);
    const now = Date.UTC(2026, 9, 7, 14);
    const a = await reserve(ddb, cfg, now, 10_000);
    if (!a.ok) throw new Error("no reservation");
    const h = later(); let armed = true;
    L.gate = (_p, k) => { if (armed && k === "reserve") { armed = false; return h.p; } return undefined; };
    const pOther = reserve(ddb, cfg, now, 10_000); // another visitor's ordinary reservation, in progress
    await waitFor(() => !armed);
    const ok = await persistBillingPause(ddb, { reason: "E_SETTLE", nowMs: now, reservedMicros: 10_000, actualMicros: 2_000_000, event: a.reservation.event });
    h.go();
    const other = await pOther;
    console.log("F2b persist", ok, "other reserve ok", other.ok, "pause?", aws.table.items.has(BILLING_PAUSE_KEY),
      "debts", [...aws.table.items.keys()].filter((k) => k.startsWith("billingdebt#")), L.log);
    expect(ok).toBe(false);
  });

  it("two bound-breach settles overlapping: second settle cancelled on billing#pause / counters", async () => {
    const aws = new FakeAws();
    const L = new Locks(aws.transport);
    const ddb = new Ddb(L.transport, cfg.region, cfg.table);
    const now = Date.UTC(2026, 9, 7, 14);
    const a = await reserve(ddb, cfg, now, 10_000); const b = await reserve(ddb, cfg, now, 10_000);
    if (!a.ok || !b.ok) throw new Error("no reservation");
    const h = later(); let armed = true;
    L.gate = (_p, k) => { if (armed && k === "settle") { armed = false; return h.p; } return undefined; };
    const pd = (r: typeof a.reservation, act: number) => ({ reason: "E_PROVIDER_BOUND" as const, nowMs: now, reservedMicros: r.micros, actualMicros: act, event: r.event });
    const s1 = settle(ddb, a.reservation, 200_000, pd(a.reservation, 200_000));
    await waitFor(() => !armed);
    const s2 = await settle(ddb, b.reservation, 300_000, pd(b.reservation, 300_000));
    const p2 = s2 ? true : await persistBillingPause(ddb, { ...pd(b.reservation, 300_000), reason: "E_SETTLE" });
    h.go();
    const r1 = await s1;
    console.log("F2c settle1", r1, "settle2", s2, "persist2 (while s1 holds pause)", p2, "month", aws.table.num(a.reservation.month, "m"),
      "debts", [...aws.table.items.keys()].filter((k) => k.startsWith("billingdebt#")), L.log);
    expect(s2).toBe(false);
  });
});
