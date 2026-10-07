// Ledger red-team (lens: ledger-logic). Offline, synthetic, no network, no AWS.
import { describe, expect, it } from "vitest";
import type { EvaluationResult } from "../../pr10b-wt/packages/explain/src/app.js";
import { Ddb } from "../../pr10b-wt/packages/explain/src/aws/dynamodb.js";
import { BILLING_PAUSE_KEY, persistBillingPause, reserve, spendKeys } from "../../pr10b-wt/packages/explain/src/spend.js";
import { FakeAws, config, evalEvent, harness, lastLog, modelReply } from "../../pr10b-wt/packages/explain/test/helpers.js";
import { LockingTransport, deferred, until } from "./lock.js";

const cfg = config();
const S = (i: unknown) => (i as { S: string }).S;
const N = (i: unknown) => Number((i as { N: string }).N);

describe("F1: an ordinary settlement TransactionConflict becomes a permanent no-TTL billing pause", () => {
  it("one overlapping reservation on the hot month/day keys stops the whole service, with zero money anomaly", async () => {
    const aws = new FakeAws();
    const lt = new LockingTransport(aws.transport);
    const hA = harness({ transport: lt.transport }); // instance A
    const hB = harness({ transport: lt.transport }); // instance B (separate memory)
    const gate = deferred();
    let calls = 0;
    aws.model = async () => {
      calls++;
      if (calls === 1) await gate.promise; // A's model call is slow
      return { status: 200, json: modelReply() }; // normal usage 820/120, well inside the reservation
    };
    const pA = hA.handler(evalEvent()) as Promise<EvaluationResult>;
    await until(() => aws.modelCalls.length === 1);
    // B's reservation transaction is in progress (holding pause/month/day/event) at the moment A settles.
    const bHolding = deferred();
    const releaseB = deferred();
    let held = false;
    lt.hold = (payload) => {
      if (!held && JSON.stringify(payload).includes("ConditionCheck")) {
        held = true;
        bHolding.resolve();
        return releaseB.promise;
      }
      return undefined;
    };
    const pB = hB.handler(evalEvent()) as Promise<EvaluationResult>;
    await bHolding.promise;
    lt.onConflict = () => releaseB.resolve(); // B finishes right after A's settlement is cancelled
    gate.resolve();
    const [a, b] = await Promise.all([pA, pB]);

    const la = JSON.parse(hA.logs.at(-1)!) as Record<string, unknown>;
    console.log("A result", a.status, a.body, "A log", la, "conflicts", lt.conflicts);
    console.log("B result", b.status, JSON.stringify(b.body).slice(0, 60));
    // A's call was fully inside its reservation: no billing anomaly occurred.
    expect(la.code).toBe("E_SETTLE");
    expect(la.actualMicros as number).toBeLessThan(la.reservedMicros as number);
    expect(la.overrun).toBeUndefined();
    expect(la.billedBoundViolated).toBeUndefined();
    // ...yet a durable, no-TTL pause now exists.
    const pause = aws.table.items.get(BILLING_PAUSE_KEY);
    console.log("pause item", pause);
    expect(pause).toBeDefined();
    expect(pause!.ttl).toBeUndefined();
    // Fresh instance, 40 days later (next month): still paused, no model call.
    const hC = harness({ transport: lt.transport });
    hC.clock.ms = hA.clock.ms + 40 * 86_400_000;
    const before = aws.modelCalls.length;
    const c = (await hC.handler(evalEvent())) as EvaluationResult;
    console.log("fresh instance 40 days later", c.status, lastLog(hC).code, new Date(hC.clock.ms).toISOString());
    expect(lastLog(hC).code).toBe("E_BILLING_PAUSE");
    expect(aws.modelCalls.length).toBe(before);
  });

  it("a release (model throttled, never billed) that conflicts also pauses permanently", async () => {
    const aws = new FakeAws();
    const lt = new LockingTransport(aws.transport);
    const h = harness({ transport: lt.transport });
    // Simulate the release transaction colliding with someone else's in-progress transaction on the day key.
    aws.model = () => {
      lt.locks.add(spendKeys(h.clock.ms).day);
      return { status: 429, errorType: "ThrottlingException" };
    };
    const r = (await h.handler(evalEvent())) as EvaluationResult;
    lt.locks.clear();
    console.log("throttled+conflict", r.status, lastLog(h));
    expect(lastLog(h).code).toBe("E_SETTLE");
    expect(lastLog(h).actualMicros).toBe(0);
    expect(aws.table.items.has(BILLING_PAUSE_KEY)).toBe(true);
  });
});

describe("F2: concurrent unresolved events conflict on the shared billing#pause key; the loser's debt is never written", () => {
  it("direct persistBillingPause race", async () => {
    const aws = new FakeAws();
    const lt = new LockingTransport(aws.transport);
    const ddb = new Ddb(lt.transport, cfg.region, cfg.table);
    const now = Date.UTC(2026, 9, 7, 14);
    const a = await reserve(ddb, cfg, now, 10_000);
    const b = await reserve(ddb, cfg, now, 10_000);
    if (!a.ok || !b.ok) throw new Error("reservation missing");
    const first = deferred();
    const release = deferred();
    let n = 0;
    lt.hold = () => (++n === 1 ? (first.resolve(), release.promise) : undefined);
    const p1 = persistBillingPause(ddb, { reason: "E_SETTLE", nowMs: now, reservedMicros: 10_000, actualMicros: 1_500_000, event: a.reservation.event });
    await first.promise;
    const r2 = await persistBillingPause(ddb, { reason: "E_SETTLE", nowMs: now, reservedMicros: 10_000, actualMicros: 1_600_000, event: b.reservation.event });
    release.resolve();
    const r1 = await p1;
    const debts = [...aws.table.items.keys()].filter((k) => k.startsWith("billingdebt#"));
    console.log("persist results", r1, r2, "debts", debts, "month m", aws.table.num(a.reservation.month, "m"));
    expect([r1, r2]).toEqual([true, false]);
    expect(debts).toEqual([`billingdebt#${a.reservation.event.slice(8)}`]);
    // b's known actual cost (1.6M micros) exists nowhere durable: counters hold only its 10k reservation, no debt row.
    expect(aws.table.num(a.reservation.month, "m")).toBe(20_000);
  });

  it("K simultaneous provider-bound breaches: only one is counted; the rest are neither in the counters nor in a debt", async () => {
    const K = 10;
    const aws = new FakeAws();
    const lt = new LockingTransport(aws.transport);
    const h = harness({ transport: lt.transport });
    const all = deferred();
    aws.model = async () => {
      if (aws.modelCalls.length >= K) all.resolve();
      await all.promise;
      // Synthetic provider breach: 30,000 billed output tokens (bound is 400).
      return { status: 200, json: modelReply({ inTok: 300, outTok: 30_000 }) };
    };
    // Reservations go through one at a time (no overlap) so all K reserve; then every settle overlaps.
    const ps: Promise<unknown>[] = [];
    for (let i = 0; i < K; i++) {
      ps.push(h.handler(evalEvent()));
      await until(() => aws.modelCalls.length === i + 1);
    }
    lt.txMs = 5; // DynamoDB transactions take a few ms; settles now overlap
    await Promise.all(ps);
    const lines = h.logs.map((l) => JSON.parse(l) as Record<string, unknown>);
    const keys = spendKeys(h.clock.ms);
    const counted = aws.table.num(keys.month, "m")!;
    const debts = [...aws.table.items.entries()].filter(([k]) => k.startsWith("billingdebt#")).map(([, v]) => N(v.actual));
    const actuals = lines.map((l) => l.actualMicros as number);
    const billed = actuals.reduce((s, x) => s + x, 0);
    const reservedEach = lines[0]!.reservedMicros as number;
    console.log({ codes: lines.map((l) => `${l.code}/p${l.pausePersisted}`), reservedEach, actualEach: actuals[0], billed, counted, debts, conflicts: lt.conflicts.length });
    const settledCount = [...aws.table.items.values()].filter((v) => v.state !== undefined && S(v.state) === "settled").length;
    const accounted = counted + debts.reduce((s, d) => s + d - reservedEach, 0);
    console.log({ settledCount, accountedDurably: accounted, unaccounted: billed - accounted });
    expect(billed - accounted).toBeGreaterThan(0);
  });
});
