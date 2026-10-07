// Ledger faults under DynamoDB transaction-conflict semantics (which the
// package's FakeTable does not model: it applies transactions one at a time).
import { describe, expect, it } from "vitest";
import type { EvaluationResult } from "../../pr10b-wt/packages/explain/src/app.js";
import { Ddb } from "../../pr10b-wt/packages/explain/src/aws/dynamodb.js";
import { BILLING_PAUSE_KEY, persistBillingPause, reserve, spendKeys } from "../../pr10b-wt/packages/explain/src/spend.js";
import { config, evalEvent, harness, httpEvent, lastLog, modelReply } from "../../pr10b-wt/packages/explain/test/helpers.js";
import { FaultAws, rng, sleep } from "./faultdb.js";

const cfg = config();
const now = Date.UTC(2026, 9, 7, 14);

describe("C1: a definite (non-ambiguous) settle cancellation", () => {
  it("TransactionConflict on settle -> durable service-wide E_SETTLE pause + debt; paid valid answer discarded", async () => {
    const fa = new FaultAws();
    fa.fault = (op, body) => op === "TransactWriteItems" && JSON.stringify(body).includes(":settled") ? "conflict" : undefined;
    const h = harness({ transport: fa.transport });
    const r = await h.handler(evalEvent()) as EvaluationResult;
    console.log("C1 result", JSON.stringify({ status: r.status, body: r.body, ev: { code: r.evaluation.code, pausePersisted: r.evaluation.pausePersisted, actual: r.evaluation.actualMicros, reserved: r.evaluation.reservedMicros } }));
    expect(r.status).toBe(503);
    expect(r.evaluation.code).toBe("E_SETTLE");
    expect(r.evaluation.pausePersisted).toBe(true);
    expect(fa.aws.table.items.has(BILLING_PAUSE_KEY)).toBe(true);
    expect(fa.items("billingdebt#")).toHaveLength(1);
    // Counters still hold the full reservation, though nothing was ambiguous.
    const keys = spendKeys(h.clock.ms);
    console.log("C1 counters", fa.aws.table.num(keys.month, "m"), fa.aws.table.num(keys.day, "m"), "actual", r.evaluation.actualMicros);
    fa.fault = undefined;
    const fresh = harness({ transport: fa.transport });
    expect((await fresh.call(httpEvent())).statusCode).toBe(503);
    expect(lastLog(fresh).code).toBe("E_BILLING_PAUSE");
  });
});

describe("C2: N instances, overlapping transactions on the shared counters", () => {
  it("measures how ordinary contention turns into durable pauses / lost debts", async () => {
    const summary: Record<string, number>[] = [];
    for (const seed of [1, 2, 3]) {
      const fa = new FaultAws();
      fa.txMs = 8;
      const rand = rng(seed);
      fa.aws.model = async () => { await sleep(Math.floor(rand() * 60)); return { status: 200, json: modelReply() }; };
      const N = 12;
      const hs = Array.from({ length: N }, () => harness({ transport: fa.transport }));
      const results = await Promise.all(hs.map(async (h, i) => { await sleep(Math.floor(rand() * 60)); return { i, r: await h.handler(evalEvent()) as EvaluationResult, h }; }));
      const codes: Record<string, number> = {};
      for (const { r } of results) codes[r.evaluation.code ?? `ok${r.status}`] = (codes[r.evaluation.code ?? `ok${r.status}`] ?? 0) + 1;
      const settleFailed = results.filter(({ r }) => r.evaluation.code === "E_SETTLE");
      const debts = fa.items("billingdebt#").length;
      const notPersisted = results.filter(({ r }) => r.evaluation.pausePersisted === false).length;
      const row = { seed, conflicts: fa.conflicts, modelCalls: fa.aws.modelCalls.length, settleFailed: settleFailed.length, debts, notPersisted, paused: fa.aws.table.items.has(BILLING_PAUSE_KEY) ? 1 : 0, ...codes };
      summary.push(row);
      // Invariant that must hold regardless: counters never exceed caps.
      const events = fa.items("billing#").filter(([k]) => k !== "billing#pause").length;
      console.log("INV modelCalls", fa.aws.modelCalls.length, "<= committed reservation events", events);
      expect(fa.aws.modelCalls.length).toBeLessThanOrEqual(events);
      const keys = spendKeys(hs[0]!.clock.ms);
      expect(fa.aws.table.num(keys.day, "m") ?? 0).toBeLessThanOrEqual(cfg.dailyMicros);
    }
    console.log("C2 summary", JSON.stringify(summary, null, 0));
    // Evidence, not an assertion on frequency: at least one run hit a settle conflict.
    expect(summary.some((s) => (s.settleFailed ?? 0) > 0)).toBe(true);
  });
});

describe("C3: durable pause write contends with another instance's reserve", () => {
  it("API level: persistBillingPause returns false and writes nothing while a reserve holds billing#pause", async () => {
    const fa = new FaultAws();
    const ddb = new Ddb(fa.transport, cfg.region, cfg.table);
    const a = await reserve(ddb, cfg, now, 10_000);
    if (!a.ok) throw new Error("no reservation");
    fa.txMs = 50;
    const b = reserve(ddb, cfg, now, 10_000); // in flight, holds billing#pause via ConditionCheck
    await sleep(5);
    const persisted = await persistBillingPause(ddb, { reason: "E_MODEL_TIMEOUT", nowMs: now, reservedMicros: 10_000, event: a.reservation.event });
    const bres = await b;
    console.log("C3 persisted", persisted, "B reserve ok", bres.ok, "pause", fa.aws.table.items.has(BILLING_PAUSE_KEY), "debts", fa.items("billingdebt#").length);
    expect(persisted).toBe(false);
    expect(bres.ok).toBe(true);
    expect(fa.aws.table.items.has(BILLING_PAUSE_KEY)).toBe(false);
    expect(fa.items("billingdebt#")).toHaveLength(0);
  });

  it("handler level: unknown-usage call A, concurrent reserve B -> no durable pause; B and a fresh C both reach the model", async () => {
    const fa = new FaultAws();
    fa.txMs = 40;
    const hA = harness({ transport: fa.transport });
    const hB = harness({ transport: fa.transport });
    let bPromise: Promise<unknown> | undefined;
    let n = 0;
    fa.aws.model = async () => {
      n++;
      if (n === 1) {
        // While A's model call is open, B starts; wait until B's reserve transaction is in flight.
        bPromise = hB.handler(evalEvent());
        for (let i = 0; i < 400 && !fa.locks.has(BILLING_PAUSE_KEY); i++) await sleep(1);
        return { status: 200, json: modelReply({ usage: null }) }; // maybe-billed: A must persist a pause
      }
      return { status: 200, json: modelReply() };
    };
    const ra = await hA.handler(evalEvent()) as EvaluationResult;
    const rb = await bPromise as EvaluationResult;
    console.log("C3h A", JSON.stringify({ status: ra.status, code: ra.evaluation.code, pausePersisted: ra.evaluation.pausePersisted }), "B", JSON.stringify({ status: rb.status, code: rb.evaluation.code, modelCalled: rb.evaluation.modelCalled }));
    expect(ra.evaluation.code).toBe("E_MODEL_NO_USAGE");
    expect(ra.evaluation.pausePersisted).toBe(false);
    expect(fa.aws.table.items.has(BILLING_PAUSE_KEY)).toBe(false);
    expect(fa.items("billingdebt#")).toHaveLength(0);
    const hC = harness({ transport: fa.transport });
    const rc = await hC.handler(evalEvent()) as EvaluationResult;
    console.log("C3h C", JSON.stringify({ status: rc.status, modelCalled: rc.evaluation.modelCalled }), "modelCalls", fa.aws.modelCalls.length,
      "unresolved reserved events", [...fa.aws.table.items.values()].filter((i) => (i.state as { S?: string } | undefined)?.S === "reserved").length);
    expect(rc.evaluation.modelCalled).toBe(true);
    expect(fa.aws.modelCalls).toHaveLength(3);
  });
});

describe("C4: two concurrent unresolved settlements persist their debts at once", () => {
  it("both transactions Put billing#pause; the loser's debt is never written", async () => {
    const fa = new FaultAws();
    const ddb = new Ddb(fa.transport, cfg.region, cfg.table);
    const a = await reserve(ddb, cfg, now, 10_000);
    const b = await reserve(ddb, cfg, now, 10_000);
    if (!a.ok || !b.ok) throw new Error("no reservation");
    fa.txMs = 20;
    const results = await Promise.all([a.reservation, b.reservation].map((r, i) => persistBillingPause(ddb, {
      reason: "E_SETTLE", nowMs: now, reservedMicros: r.micros, actualMicros: 15_000 + i, event: r.event })));
    console.log("C4 results", JSON.stringify(results), "debts", fa.items("billingdebt#").map(([, it]) => (it.actual as { N: string }).N));
    // Package test (serial fake) expects [true,true] and two debts.
    expect(results).toEqual([true, false]);
    expect(fa.items("billingdebt#")).toHaveLength(1);
  });
});
