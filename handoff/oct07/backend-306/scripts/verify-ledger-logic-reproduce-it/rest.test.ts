// Independent reproduction of F3..F9 (offline; FakeAws; virtual clock; no network).
import { describe, expect, it } from "vitest";
import type { EvaluationResult } from "../../pr10b-wt/packages/explain/src/app.js";
import { Ddb, DDB_TIMEOUT_MS } from "../../pr10b-wt/packages/explain/src/aws/dynamodb.js";
import { MODEL_TIMEOUT_MS, converseModel, modelRequest } from "../../pr10b-wt/packages/explain/src/aws/bedrock.js";
import { TransportError, type AwsCall, type Transport } from "../../pr10b-wt/packages/explain/src/aws/transport.js";
import { BILLING_PAUSE_KEY, actualMicros, persistBillingPause, reserve, settle, spendKeys } from "../../pr10b-wt/packages/explain/src/spend.js";
import { FakeAws, STUB_MODELS, config, evalEvent, harness, lastLog, modelReply } from "../../pr10b-wt/packages/explain/test/helpers.js";
import { later, waitFor } from "./ddblock.js";

const usd = (m: number) => `$${(m / 1e6).toFixed(6)}`;

describe("F3 time budget", () => {
  function timed(h: ReturnType<typeof harness>, plan: (op: string, body: string) => { ms: number; fail?: boolean }, trace: string[]): Transport {
    const inner = h.aws.transport;
    const t0 = h.clock.ms;
    return async (call: AwsCall) => {
      const op = call.service === "dynamodb" ? (call.headers["x-amz-target"] ?? "").split(".")[1]! : call.host.startsWith("bedrock-runtime") ? "Converse" : "settings";
      const p = plan(op, call.body ?? "");
      const s = h.clock.ms - t0;
      h.clock.ms += p.ms;
      trace.push(`${(s / 1000).toFixed(2)}->${((h.clock.ms - t0) / 1000).toFixed(2)} ${op}${call.body?.includes(":settled") ? "(settle)" : call.body?.includes("billingdebt") ? "(persist)" : call.body?.includes("ConditionCheck") ? "(reserve)" : ""}${p.fail ? " TIMEOUT" : ""}`);
      if (p.fail) throw new TransportError("timeout");
      return inner(call);
    };
  }
  it("static: code's own post-call chain exceeds the 28 s Lambda Timeout", () => {
    console.log("F3 static", { MODEL_TIMEOUT_MS, DDB_TIMEOUT_MS, unknownUsageChain: MODEL_TIMEOUT_MS + 3 * DDB_TIMEOUT_MS, settleFailChain: MODEL_TIMEOUT_MS + 6 * DDB_TIMEOUT_MS });
    expect(MODEL_TIMEOUT_MS + 3 * DDB_TIMEOUT_MS).toBeGreaterThan(28_000);
  });
  it("unknown usage (model timeout) + slow DynamoDB: log line and in-memory pause would land after 28 s", async () => {
    const h = harness();
    h.aws.model = () => "timeout";
    const trace: string[] = [];
    let after = false;
    h.deps.transport = timed(h, (op, body) => {
      if (op === "Converse") { after = true; return { ms: MODEL_TIMEOUT_MS, fail: true }; }
      if (after && op === "TransactWriteItems" && body.includes("billingdebt")) return { ms: DDB_TIMEOUT_MS, fail: true };
      if (after) return { ms: 2_800 };
      return { ms: 30 };
    }, trace);
    const r = (await h.handler(evalEvent())) as EvaluationResult;
    console.log("F3 trace\n" + trace.join("\n"), "\nresult", r.status, lastLog(h).code, "pausePersisted", lastLog(h).pausePersisted, "elapsed ms", lastLog(h).ms);
    expect(lastLog(h).ms as number).toBeGreaterThan(28_000);
  });
  it("slow pre-call (degraded DynamoDB) leaves < 20 s for the model: Lambda would kill mid-call (no pause, no app log)", async () => {
    const h = harness();
    const trace: string[] = [];
    h.deps.transport = timed(h, (op) => (op === "Converse" ? { ms: 19_000 } : op === "settings" ? { ms: 100 } : { ms: 1_200 }), trace);
    await h.handler(evalEvent());
    const conv = trace.find((t) => t.includes("Converse"))!;
    console.log("F3 pre-call trace\n" + trace.join("\n"));
    console.log("Converse start s", conv.split("->")[0]);
  });
});

describe("F4 overshoot scales with in-flight count", () => {
  async function run(K: number, outTok: number, env: Record<string, string>) {
    const p = harness({ env }); await p.handler(evalEvent()); const R = lastLog(p).reservedMicros as number;
    const h = harness({ env });
    const k = spendKeys(h.clock.ms);
    const cap = h.deps.config!.capMicros;
    h.aws.table.items.set(k.month, { pk: { S: k.month }, m: { N: String(cap - K * R) } });
    const g = later();
    h.aws.model = async () => { if (h.aws.modelCalls.length >= K) g.go(); await g.p; return { status: 200, json: modelReply({ inTok: 300, outTok }) }; };
    await Promise.all(Array.from({ length: K }, () => h.handler(evalEvent())));
    const next = (await h.handler(evalEvent())) as EvaluationResult;
    const per = actualMicros(300, outTok, h.deps.config!);
    return { R, per, month: h.aws.table.num(k.month, "m")!, calls: h.aws.modelCalls.length, next: next.status, codes: h.logs.map((l) => (JSON.parse(l) as { code: string }).code) };
  }
  for (const K of [1, 5]) it(`sonnet-priced K=${K}`, async () => {
    const r = await run(K, 128_000, { EXPLAIN_MODEL_ID: "us.anthropic.claude-sonnet-5-5", EXPLAIN_PRICE_OUT: "11" });
    console.log(`F4 K=${K} R=${r.R} perCallActual=${usd(r.per)} month=${usd(r.month)} expected cap+K*(per-R)=${usd(25_000_000 + K * (r.per - r.R))} calls=${r.calls} next=${r.next} codes=${r.codes.join(",")}`);
    expect(r.month).toBe(25_000_000 + K * (r.per - r.R));
  });
});

describe("F5 debts are outside headroom", () => {
  it("after the owner deletes billing#pause the full cap is reservable again", async () => {
    const aws = new FakeAws(); const cfg = config(); const ddb = new Ddb(aws.transport, cfg.region, cfg.table);
    const now = Date.UTC(2026, 9, 7, 14);
    const r = await reserve(ddb, cfg, now, 10_000); if (!r.ok) throw new Error();
    expect(await persistBillingPause(ddb, { reason: "E_SETTLE", nowMs: now, reservedMicros: 10_000, actualMicros: 2_000_000, event: r.reservation.event })).toBe(true);
    expect((await reserve(ddb, cfg, now, 1)).ok).toBe(false);
    aws.table.items.delete(BILLING_PAUSE_KEY);
    // Remaining day headroom equals daily limit minus only the 10,000 reservation; the $2.00 debt is invisible.
    const big = await reserve(ddb, cfg, now, cfg.dailyMicros - 10_000);
    console.log("F5 daily", cfg.dailyMicros, "reserve(daily-10k) ok?", big.ok, "debt rows", [...aws.table.items.keys()].filter((k) => k.startsWith("billingdebt#")).length);
    expect(big.ok).toBe(true);
  });
});

describe("F6/F7 late commits", () => {
  it("F6 reservation applied after the recovery read", async () => {
    const h = harness(); const inner = h.aws.transport; let late: (() => Promise<unknown>) | undefined;
    h.deps.transport = async (c) => { if (c.service === "dynamodb" && c.body.includes("ConditionCheck") && !late) { late = () => inner(c); throw new TransportError("timeout"); } return inner(c); };
    await h.handler(evalEvent()); await late!();
    const k = spendKeys(h.clock.ms);
    const ev = [...h.aws.table.items.entries()].filter(([x]) => x.startsWith("billing#"));
    console.log("F6", lastLog(h).code, "modelCalls", h.aws.modelCalls.length, "month", h.aws.table.num(k.month, "m"), "events", ev.map(([x, v]) => `${x.slice(0, 14)} ${(v.state as { S: string }).S} ttl=${(v.ttl as { N: string }).N}`), "pause?", h.aws.table.items.has(BILLING_PAUSE_KEY));
    expect(h.aws.modelCalls.length).toBe(0);
  });
  it("F7 settle applied after the recovery read; debt also written", async () => {
    const h = harness(); const inner = h.aws.transport; let late: (() => Promise<unknown>) | undefined;
    h.deps.transport = async (c) => { if (c.service === "dynamodb" && c.body.includes(":settled") && !late) { late = () => inner(c); throw new TransportError("timeout"); } return inner(c); };
    await h.handler(evalEvent()); const lg = lastLog(h); await late!();
    const k = spendKeys(h.clock.ms);
    const debt = [...h.aws.table.items.entries()].find(([x]) => x.startsWith("billingdebt#"))?.[1];
    const ev = [...h.aws.table.items.entries()].find(([x]) => x.startsWith("billing#") && x !== BILLING_PAUSE_KEY)?.[1];
    console.log("F7", lg.code, "actual", lg.actualMicros, "reserved", lg.reservedMicros, "month", h.aws.table.num(k.month, "m"), "debt", debt?.actual, debt?.reserved, "event", ev?.state, ev?.actual);
  });
});

describe("F8 settled breach evidence", () => {
  it("two in-flight breaches settle sequentially (no conflict modelled): pause keeps last, no debt rows", async () => {
    const h = harness(); const g = later();
    h.aws.model = async () => { if (h.aws.modelCalls.length >= 2) g.go(); await g.p; return { status: 200, json: modelReply({ inTok: 300, outTok: 30_000 }) }; };
    await Promise.all([h.handler(evalEvent()), h.handler(evalEvent())]);
    const pause = h.aws.table.items.get(BILLING_PAUSE_KEY)!;
    const evs = [...h.aws.table.items.entries()].filter(([x]) => x.startsWith("billing#") && x !== BILLING_PAUSE_KEY);
    console.log("F8 pause.event", (pause.event as { S: string }).S, "events", evs.map(([x, v]) => `${x} ${(v.state as { S: string }).S} actual=${(v.actual as { N: string }).N} ttl=${(v.ttl as { N: string }).N}`), "debts", [...h.aws.table.items.keys()].filter((x) => x.startsWith("billingdebt#")).length, "codes", h.logs.map((l) => JSON.parse(l).code));
  });
});

describe("F9 cache write pricing", () => {
  it("cacheWriteInputTokens charged at 1x input", async () => {
    const id = "us.anthropic.claude-sonnet-5-5"; const m = STUB_MODELS[id]!;
    const body = { output: { message: { role: "assistant", content: [{ text: "x" }] } }, stopReason: "end_turn", usage: { inputTokens: 100, outputTokens: 50, cacheWriteInputTokens: 2000, cacheReadInputTokens: 0, totalTokens: 2150 } };
    const o = await converseModel(async () => ({ status: 200, headers: {}, body: JSON.stringify(body) }), m.region, id, modelRequest("s", "u", m), m);
    if (o.kind !== "reply") throw new Error(o.kind);
    const cfg = config({ EXPLAIN_MODEL_ID: id, EXPLAIN_PRICE_OUT: "11" });
    console.log("F9 inTok", o.inTok, "charged", actualMicros(o.inTok, o.outTok, cfg), "at1.25x", Math.ceil((100 * 2200 + 2000 * 2750 + 50 * 11000) / 1000));
    const req = JSON.stringify(modelRequest("s", "u", m));
    console.log("F9 request has cachePoint?", req.includes("cachePoint"), "requestFields", JSON.stringify(m.requestFields));
  });
});
