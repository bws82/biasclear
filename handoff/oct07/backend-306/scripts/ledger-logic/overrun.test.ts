// F4 (worst case vs the disclosed $26.40), F5 (debt outside headroom), F6/F7 (late commits), F8 (breach evidence).
import { describe, expect, it } from "vitest";
import type { EvaluationResult } from "../../pr10b-wt/packages/explain/src/app.js";
import { Ddb } from "../../pr10b-wt/packages/explain/src/aws/dynamodb.js";
import { TransportError, type Transport } from "../../pr10b-wt/packages/explain/src/aws/transport.js";
import { BILLING_PAUSE_KEY, persistBillingPause, reserve, settle, spendKeys } from "../../pr10b-wt/packages/explain/src/spend.js";
import { FakeAws, config, evalEvent, harness, lastLog, modelReply } from "../../pr10b-wt/packages/explain/test/helpers.js";
import { until, deferred } from "./lock.js";

const usd = (m: number) => `$${(m / 1e6).toFixed(6)}`;

async function concurrentBreaches(K: number, env: Record<string, string>, outTok: number) {
  // Probe the reservation size for the fixed fixture sentence.
  const probe = harness({ env });
  await probe.handler(evalEvent());
  const R = lastLog(probe).reservedMicros as number;

  const h = harness({ env });
  const keys = spendKeys(h.clock.ms);
  const cap = h.deps.config!.capMicros;
  // The month is already full except for exactly K reservations.
  h.aws.table.items.set(keys.month, { pk: { S: keys.month }, m: { N: String(cap - K * R) } });
  const all = deferred();
  h.aws.model = async () => {
    if (h.aws.modelCalls.length >= K) all.resolve();
    await all.promise;
    return { status: 200, json: modelReply({ inTok: 300, outTok }) };
  };
  const ps: Promise<unknown>[] = [];
  for (let i = 0; i < K; i++) ps.push(h.handler(evalEvent()));
  await Promise.all(ps);
  // One more request after the anomaly: correctly paused.
  const after = (await h.handler(evalEvent())) as EvaluationResult;
  return { h, R, month: h.aws.table.num(keys.month, "m")!, day: h.aws.table.num(keys.day, "m")!, calls: h.aws.modelCalls.length, after: after.status };
}

describe("F4: the overrun is not bounded by a single breach; every in-flight reservation can breach before detection", () => {
  for (const [label, env] of [["grok-priced stub", {}], ["sonnet/sol-priced stub ($11/M out)", { EXPLAIN_MODEL_ID: "us.anthropic.claude-sonnet-5-5", EXPLAIN_PRICE_OUT: "11" }]] as const) {
    for (const K of [1, 10, 61]) {
      it(`${label}: K=${K} in-flight calls, each billing 128,000 output tokens`, async () => {
        const r = await concurrentBreaches(K, env, 128_000);
        console.log(`${label} K=${K}: reservation ${usd(r.R)} each; model calls ${r.calls}; month counter ${usd(r.month)} (cap $25); day counter ${usd(r.day)} (daily $2.50); next request status ${r.after}`);
        expect(r.calls).toBe(K);
        expect(r.after).toBe(503);
        if (K > 1) expect(r.month).toBeGreaterThan(26_400_003);
      });
    }
  }
});

describe("F5: an unresolved debt is never counted against headroom once the pause is removed", () => {
  it("clearing billing#pause (the only way back) re-opens the full cap although a $1.99 debt is recorded", async () => {
    const aws = new FakeAws();
    const cfg = config();
    const ddb = new Ddb(aws.transport, cfg.region, cfg.table);
    const now = Date.UTC(2026, 9, 7, 14);
    const r = await reserve(ddb, cfg, now, 10_000);
    if (!r.ok) throw new Error("x");
    // Settlement failed; the known actual charge goes into the debt row only.
    expect(await persistBillingPause(ddb, { reason: "E_SETTLE", nowMs: now, reservedMicros: 10_000, actualMicros: 2_000_000, event: r.reservation.event })).toBe(true);
    // Owner clears the pause (no repo procedure/tool says to add the debt delta to the counters first).
    aws.table.items.delete(BILLING_PAUSE_KEY);
    let granted = 0;
    for (let day = 7; day <= 31; day++) {
      const t = Date.UTC(2026, 9, day, 15);
      for (;;) {
        const x = await reserve(ddb, cfg, t, 9_205);
        if (!x.ok) break;
        await settle(ddb, x.reservation, 9_205);
        granted += 9_205;
      }
    }
    const month = aws.table.num(spendKeys(now).month, "m")!;
    const real = granted + 2_000_000;
    console.log(`month counter ${usd(month)}; real month spend incl. debt ${usd(real)}; debt rows ${[...aws.table.items.keys()].filter((k) => k.startsWith("billingdebt#")).length}`);
    expect(real).toBeGreaterThan(cfg.capMicros);
  });
});

describe("F6/F7: a transaction that commits after the consistent recovery read", () => {
  it("F6 reserve: request is refused (E_DDB) but the reservation commits later and is never released, settled or recorded as debt", async () => {
    const h = harness();
    const inner = h.aws.transport;
    let late: (() => Promise<unknown>) | undefined;
    h.deps.transport = (async (call) => {
      if (call.service === "dynamodb" && call.body.includes("ConditionCheck") && late === undefined) {
        late = () => inner(call); // DynamoDB still applies it after our 3 s client timeout
        throw new TransportError("timeout");
      }
      return inner(call);
    }) as Transport;
    const res = (await h.handler(evalEvent())) as EvaluationResult;
    await late!();
    const keys = spendKeys(h.clock.ms);
    const events = [...h.aws.table.items.entries()].filter(([k]) => k.startsWith("billing#"));
    console.log("status", res.status, lastLog(h).code, "model calls", h.aws.modelCalls.length, "month", h.aws.table.num(keys.month, "m"), "day", h.aws.table.num(keys.day, "m"), "events", events.map(([k, v]) => `${k.slice(0, 16)}:${(v.state as { S: string }).S}`));
    expect(lastLog(h).code).toBe("E_DDB");
    expect(h.aws.modelCalls).toHaveLength(0);
    expect(h.aws.table.num(keys.month, "m")).toBeGreaterThan(0);
  });

  it("F7 settle: recovery read sees 'reserved', a debt with the actual is written, then the settle commits too", async () => {
    const h = harness();
    const inner = h.aws.transport;
    let late: (() => Promise<unknown>) | undefined;
    h.aws.model = () => ({ status: 200, json: modelReply({ inTok: 300, outTok: 30_000 }) });
    h.deps.transport = (async (call) => {
      if (call.service === "dynamodb" && call.body.includes(":settled") && late === undefined) {
        late = () => inner(call);
        throw new TransportError("timeout");
      }
      return inner(call);
    }) as Transport;
    await h.handler(evalEvent());
    await late!();
    const keys = spendKeys(h.clock.ms);
    const debt = [...h.aws.table.items.entries()].find(([k]) => k.startsWith("billingdebt#"))?.[1];
    const ev = [...h.aws.table.items.entries()].find(([k]) => k.startsWith("billing#") && k !== BILLING_PAUSE_KEY)?.[1];
    console.log("log", lastLog(h).code, "month", h.aws.table.num(keys.month, "m"), "debt actual", debt?.actual, "debt reserved", debt?.reserved, "event state", ev?.state);
    // Counter already includes the actual; the 'unresolved' debt also carries it: naive reconciliation double-counts.
    expect(h.aws.table.num(keys.month, "m")).toBe(Number((debt!.actual as { N: string }).N));
  });
});

describe("F8: settled bound breaches leave no billingdebt row; the single pause row keeps only the last event", () => {
  it("two in-flight breaches", async () => {
    const h = harness();
    const all = deferred();
    h.aws.model = async () => {
      if (h.aws.modelCalls.length >= 2) all.resolve();
      await all.promise;
      return { status: 200, json: modelReply({ inTok: 300, outTok: 30_000 }) };
    };
    await Promise.all([h.handler(evalEvent()), h.handler(evalEvent())]);
    const pause = h.aws.table.items.get(BILLING_PAUSE_KEY)!;
    const debts = [...h.aws.table.items.keys()].filter((k) => k.startsWith("billingdebt#"));
    const evs = [...h.aws.table.items.entries()].filter(([k]) => k.startsWith("billing#") && k !== BILLING_PAUSE_KEY);
    console.log("pause.event", (pause.event as { S: string }).S.slice(0, 20), "debt rows", debts.length, "breach events", evs.map(([k, v]) => `${k.slice(0, 20)} ttl=${(v.ttl as { N: string }).N}`));
    expect(debts).toHaveLength(0);
    expect(evs).toHaveLength(2);
  });
});
