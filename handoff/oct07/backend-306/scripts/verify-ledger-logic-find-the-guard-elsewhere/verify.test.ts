// Independent verification (angle: find-the-guard-elsewhere). Offline, synthetic, no network/AWS.
import { describe, expect, it } from "vitest";
import type { EvaluationResult } from "../../pr10b-wt/packages/explain/src/app.js";
import { Ddb, DDB_TIMEOUT_MS } from "../../pr10b-wt/packages/explain/src/aws/dynamodb.js";
import { MODEL_TIMEOUT_MS } from "../../pr10b-wt/packages/explain/src/aws/bedrock.js";
import { TransportError, type AwsCall, type AwsReply, type Transport } from "../../pr10b-wt/packages/explain/src/aws/transport.js";
import { BILLING_PAUSE_KEY, persistBillingPause, reserve, settle, spendKeys } from "../../pr10b-wt/packages/explain/src/spend.js";
import { FakeAws, config, evalEvent, harness, lastLog, modelReply } from "../../pr10b-wt/packages/explain/test/helpers.js";

const cfg = config();
const opOf = (c: AwsCall) => (c.headers["x-amz-target"] ?? "").replace("DynamoDB_20120810.", "");
const keysOf = (body: Record<string, unknown>): string[] =>
  (body.TransactItems as Record<string, Record<string, unknown>>[]).map((it) => {
    const b = Object.values(it)[0] as { Key?: { pk: { S: string } }; Item?: { pk: { S: string } } };
    return (b.Key ?? b.Item)!.pk.S;
  });
const conflictReply = (keys: string[], hot: Set<string>): AwsReply => ({
  status: 400, headers: {},
  body: JSON.stringify({ __type: "com.amazonaws.dynamodb.v20120810#TransactionCanceledException",
    CancellationReasons: keys.map((k) => ({ Code: hot.has(k) ? "TransactionConflict" : "None" })) }),
});

describe("F1 settlement conflict -> durable pause", () => {
  it("normal answer, settle cancelled with TransactionConflict (nothing applied) -> E_SETTLE + no-TTL pause", async () => {
    const aws = new FakeAws();
    let injected = 0;
    const t: Transport = async (call) => {
      if (call.service === "dynamodb" && opOf(call) === "TransactWriteItems" && call.body.includes(":settled") && injected === 0) {
        injected++;
        const body = JSON.parse(call.body) as Record<string, unknown>;
        return conflictReply(keysOf(body), new Set(Object.values(spendKeys(Date.UTC(2026, 9, 5, 14, 3)))));
      }
      return aws.transport(call);
    };
    const h = harness({ transport: t });
    const r = (await h.handler(evalEvent())) as EvaluationResult;
    const log = lastLog(h);
    const pause = aws.table.items.get(BILLING_PAUSE_KEY);
    console.log("F1a", r.status, log, pause);
    expect(log.code).toBe("E_SETTLE");
    expect(log.actualMicros as number).toBeLessThan(log.reservedMicros as number);
    expect(log.billedBoundViolated).toBeUndefined();
    expect(pause?.ttl).toBeUndefined();
    expect(pause).toBeDefined();
    // a fresh instance next month is still stopped
    const h2 = harness({ transport: aws.transport });
    h2.clock.ms += 40 * 86_400_000;
    const before = aws.modelCalls.length;
    await h2.handler(evalEvent());
    console.log("F1a fresh", lastLog(h2).code);
    expect(lastLog(h2).code).toBe("E_BILLING_PAUSE");
    expect(aws.modelCalls.length).toBe(before);
  });

  it("a 429 (not billed) whose release conflicts also durably pauses", async () => {
    const aws = new FakeAws();
    aws.model = () => ({ status: 429, errorType: "ThrottlingException" });
    let injected = 0;
    const t: Transport = async (call) => {
      if (call.service === "dynamodb" && opOf(call) === "TransactWriteItems" && call.body.includes(":settled") && injected++ === 0) {
        const body = JSON.parse(call.body) as Record<string, unknown>;
        return conflictReply(keysOf(body), new Set([keysOf(body)[2]!]));
      }
      return aws.transport(call);
    };
    const h = harness({ transport: t });
    await h.handler(evalEvent());
    console.log("F1b", lastLog(h));
    expect(lastLog(h).code).toBe("E_SETTLE");
    expect(aws.table.items.has(BILLING_PAUSE_KEY)).toBe(true);
  });

  it("contrast: a RESERVE conflict is an E_DDB refusal, no pause (the only conflict the SPEC accepts)", async () => {
    const aws = new FakeAws();
    let injected = 0;
    const t: Transport = async (call) => {
      if (call.service === "dynamodb" && opOf(call) === "TransactWriteItems" && call.body.includes("ConditionCheck") && injected++ === 0) {
        const body = JSON.parse(call.body) as Record<string, unknown>;
        return conflictReply(keysOf(body), new Set([keysOf(body)[1]!]));
      }
      return aws.transport(call);
    };
    const h = harness({ transport: t });
    await h.handler(evalEvent());
    console.log("F1c", lastLog(h).code, aws.table.items.has(BILLING_PAUSE_KEY));
    expect(lastLog(h).code).toBe("E_DDB");
    expect(aws.table.items.has(BILLING_PAUSE_KEY)).toBe(false);
  });
});

/** Minimal lock model: a TransactWriteItems in progress holds its keys; an overlapping one is cancelled. */
function locking(inner: Transport, holdMs: () => number) {
  const locks = new Set<string>();
  const log: string[] = [];
  const t: Transport = async (call) => {
    if (call.service !== "dynamodb" || opOf(call) !== "TransactWriteItems") return inner(call);
    const keys = keysOf(JSON.parse(call.body) as Record<string, unknown>);
    const hot = keys.filter((k) => locks.has(k));
    if (hot.length) { log.push(`conflict on ${hot.join(",")}`); return conflictReply(keys, new Set(hot)); }
    keys.forEach((k) => locks.add(k));
    try {
      const ms = holdMs();
      if (ms > 0) await new Promise((r) => setTimeout(r, ms));
      return await inner(call);
    } finally { keys.forEach((k) => locks.delete(k)); }
  };
  return { t, log };
}

describe("F2 debt shares a transaction with the shared pause item", () => {
  it("two concurrent persistBillingPause: loser stores neither pause nor debt", async () => {
    const aws = new FakeAws();
    const { t, log } = locking(aws.transport, () => 5);
    const ddb = new Ddb(t, cfg.region, cfg.table);
    const now = Date.UTC(2026, 9, 7, 14);
    const a = await reserve(ddb, cfg, now, 10_000); const b = await reserve(ddb, cfg, now, 10_000);
    if (!a.ok || !b.ok) throw new Error("x");
    const res = await Promise.all([a, b].map((r, i) => persistBillingPause(ddb, { reason: "E_SETTLE", nowMs: now,
      reservedMicros: 10_000, actualMicros: 1_500_000 + i, event: r.ok ? r.reservation.event : "" })));
    const debts = [...aws.table.items.keys()].filter((k) => k.startsWith("billingdebt#"));
    console.log("F2a", res, debts, log, "month", aws.table.num(a.reservation.month, "m"));
    expect(res.filter(Boolean)).toHaveLength(1);
    expect(debts).toHaveLength(1);
  });

  it("extension: persistBillingPause also conflicts with an ordinary concurrent reserve (ConditionCheck on billing#pause)", async () => {
    const aws = new FakeAws();
    let first = true;
    const { t, log } = locking(aws.transport, () => (first ? (first = false, 20) : 0));
    const ddb = new Ddb(t, cfg.region, cfg.table);
    const now = Date.UTC(2026, 9, 7, 14);
    const a = await reserve(ddb, cfg, now, 10_000); if (!a.ok) throw new Error("x");
    first = true;
    const pr = reserve(ddb, cfg, now, 10_000); // in progress, holding billing#pause via ConditionCheck
    await new Promise((r) => setTimeout(r, 2));
    const persisted = await persistBillingPause(ddb, { reason: "E_SETTLE", nowMs: now, reservedMicros: 10_000, actualMicros: 50_000, event: a.reservation.event });
    const r2 = await pr;
    console.log("F2b persisted", persisted, "concurrent reserve ok", r2.ok, log, "pause?", aws.table.items.has(BILLING_PAUSE_KEY));
    expect(persisted).toBe(false);
  });
});

describe("F3 time budget", () => {
  async function postModelDdbCalls(model: FakeAws["model"]): Promise<{ n: number; code: unknown; log: Record<string, unknown> }> {
    const aws = new FakeAws();
    aws.model = model;
    let after = false; let n = 0;
    const t: Transport = async (call) => {
      if (call.host.startsWith("bedrock-runtime.")) { const r = await aws.transport(call); after = true; return r; }
      if (after && call.service === "dynamodb") { n++; throw new TransportError("timeout"); }
      return aws.transport(call);
    };
    const h = harness({ transport: t });
    await h.handler(evalEvent());
    return { n, code: lastLog(h).code, log: lastLog(h) };
  }
  it("worst sequential post-model DynamoDB chain vs Lambda Timeout 28 s", async () => {
    const ok = await postModelDdbCalls(() => ({ status: 200, json: modelReply() }));
    const breach = await postModelDdbCalls(() => ({ status: 200, json: modelReply({ inTok: 300, outTok: 30_000 }) }));
    const unknown = await postModelDdbCalls(() => "timeout");
    console.log("F3", { ok: ok.n, breach: breach.n, unknown: unknown.n, codes: [ok.code, breach.code, unknown.code],
      modelMs: MODEL_TIMEOUT_MS, ddbMs: DDB_TIMEOUT_MS,
      worstOk: MODEL_TIMEOUT_MS + ok.n * DDB_TIMEOUT_MS, worstBreach: MODEL_TIMEOUT_MS + breach.n * DDB_TIMEOUT_MS,
      worstUnknown: MODEL_TIMEOUT_MS + unknown.n * DDB_TIMEOUT_MS });
    expect(MODEL_TIMEOUT_MS + ok.n * DDB_TIMEOUT_MS).toBeGreaterThan(28_000);
  });
});

describe("F6/F7 late commits", () => {
  it("F6: reserve tx applied after the read-back", async () => {
    const aws = new FakeAws();
    let pending: (() => Promise<unknown>) | undefined;
    const t: Transport = async (call) => {
      if (call.service === "dynamodb" && opOf(call) === "TransactWriteItems" && call.body.includes("ConditionCheck") && pending === undefined) {
        pending = () => aws.transport(call);
        throw new TransportError("timeout");
      }
      return aws.transport(call);
    };
    const ddb = new Ddb(t, cfg.region, cfg.table);
    const now = Date.UTC(2026, 9, 7, 14);
    let err: unknown; try { await reserve(ddb, cfg, now, 9205); } catch (e) { err = e; }
    await pending!();
    const k = spendKeys(now);
    const events = [...aws.table.items.entries()].filter(([key]) => key.startsWith("billing#"));
    console.log("F6", String(err), aws.table.num(k.month, "m"), events.map(([key, v]) => [key, v.state]));
    expect(aws.table.num(k.month, "m")).toBe(9205);
  });
  it("F7: settle applied after read-back -> debt + settled event", async () => {
    const aws = new FakeAws();
    let pending: (() => Promise<unknown>) | undefined;
    const t: Transport = async (call) => {
      if (call.service === "dynamodb" && opOf(call) === "TransactWriteItems" && call.body.includes(":settled") && pending === undefined) {
        pending = () => aws.transport(call);
        throw new TransportError("timeout");
      }
      return aws.transport(call);
    };
    const ddb = new Ddb(t, cfg.region, cfg.table);
    const now = Date.UTC(2026, 9, 7, 14);
    const r = await reserve(ddb, cfg, now, 9205); if (!r.ok) throw new Error("x");
    const ok = await settle(ddb, r.reservation, 198_660);
    const p = await persistBillingPause(ddb, { reason: "E_SETTLE", nowMs: now, reservedMicros: 9205, actualMicros: 198_660, event: r.reservation.event });
    await pending!();
    const k = spendKeys(now);
    const debt = [...aws.table.items.entries()].find(([key]) => key.startsWith("billingdebt#"));
    console.log("F7", ok, p, aws.table.num(k.month, "m"), debt?.[1].actual, aws.table.items.get(r.reservation.event)?.state);
    expect(ok).toBe(false);
    expect(aws.table.num(k.month, "m")).toBe(198_660);
  });
});
