// Lambda Timeout is 28 s (infra/aws/explain.yaml). Each AWS call has its own
// timeout (DDB 3 s, settings 3 s, model 20 s) but the handler never checks the
// remaining invocation time. Latencies are scaled 1 real ms = 100 virtual ms.
import { beforeAll, describe, expect, it } from "vitest";
import type { EvaluationResult } from "../../pr10b-wt/packages/explain/src/app.js";
import { DDB_TIMEOUT_MS } from "../../pr10b-wt/packages/explain/src/aws/dynamodb.js";
import { MODEL_TIMEOUT_MS, SETTINGS_TIMEOUT_MS } from "../../pr10b-wt/packages/explain/src/aws/bedrock.js";
import type { Transport } from "../../pr10b-wt/packages/explain/src/aws/transport.js";
import { BILLING_PAUSE_KEY, spendKeys } from "../../pr10b-wt/packages/explain/src/spend.js";
import { evalEvent, harness, httpEvent, lastLog, modelReply } from "../../pr10b-wt/packages/explain/test/helpers.js";
import { FaultAws, opOf, sleep } from "./faultdb.js";

const SCALE = 100;
const LAMBDA_TIMEOUT_MS = 28_000;

function timeline(fa: FaultAws) {
  const t0 = { v: 0 };
  const marks: { at: number; what: string }[] = [];
  const inner = fa.transport;
  const transport: Transport = async (call) => {
    const at = Math.round((performance.now() - t0.v) * SCALE);
    const what = call.service === "dynamodb" ? `ddb:${opOf(call)}${opOf(call) === "TransactWriteItems" ? (call.body.includes(":settled") ? "(settle)" : call.body.includes("ConditionCheck") ? "(reserve)" : "(pause)") : ""}`
      : call.host.startsWith("bedrock-runtime.") ? "model" : `settings:${call.path}`;
    marks.push({ at, what: `${what} start` });
    try { return await inner(call); } finally { marks.push({ at: Math.round((performance.now() - t0.v) * SCALE), what: `${what} end` }); }
  };
  return { t0, marks, transport };
}

describe("D1: the handler's own worst-case path exceeds the 28 s Lambda timeout", () => {
  // Warm the rule engine so CPU time is not scaled into the virtual timeline.
  beforeAll(async () => { const fa = new FaultAws(); await harness({ transport: fa.transport }).call(httpEvent()); });
  it("prints the constants", () => {
    console.log("timeouts", { DDB_TIMEOUT_MS, SETTINGS_TIMEOUT_MS, MODEL_TIMEOUT_MS, LAMBDA_TIMEOUT_MS });
    expect(MODEL_TIMEOUT_MS).toBe(20_000);
  });

  for (const [name, ddb, settings, model, usageNull] of [
    ["every call just under its timeout", 29, 29, 199, false],
    ["DDB ~1.4 s, settings ~1.4 s, model times out at 20 s", 14, 14, 200, true],
    ["DDB ~1 s brownout, slow but valid model", 10, 10, 195, false],
    ["DDB ~1 s brownout, model times out (maybe-billed -> needs durable pause)", 10, 10, 200, true],
  ] as const) it(name, async () => {
    const fa = new FaultAws();
    fa.latency = { ddb, settings, model };
    if (usageNull) fa.aws.model = () => ({ status: 200, json: modelReply({ usage: null }) });
    const tl = timeline(fa);
    const h = harness({ transport: tl.transport });
    tl.t0.v = performance.now();
    // Web request (rate limits + first-request-of-day salt), the normal path.
    const r = await h.call(httpEvent());
    const crit = tl.marks.filter((m) => /model|settle|pause|reserve/.test(m.what));
    console.log(`D1 ${name}:`, r.statusCode, lastLog(h).code ?? "ok", JSON.stringify(crit));
    const modelEnd = tl.marks.find((m) => m.what === "model end")!.at;
    const last = tl.marks.at(-1)!.at;
    console.log(`   model ends at ~${(modelEnd / 1000).toFixed(1)} s; last ledger write ends at ~${(last / 1000).toFixed(1)} s; Lambda limit 28 s`);
    expect(last).toBeGreaterThan(LAMBDA_TIMEOUT_MS);
  });
});

describe("D2: what a Lambda kill after the model call leaves behind", () => {
  for (const where of ["model call open", "settle transaction open"] as const) it(`killed with the ${where}`, async () => {
    const fa = new FaultAws();
    const h = harness({ transport: fa.transport });
    if (where === "model call open") fa.aws.model = () => new Promise(() => undefined); // never answers
    else fa.fault = (op, body) => op === "TransactWriteItems" && JSON.stringify(body).includes(":settled") ? "hang" : undefined;
    void h.handler(evalEvent()); // the runtime freezes/kills the instance at 28 s; nothing after runs
    await sleep(50);
    expect(fa.aws.modelCalls).toHaveLength(1);
    const keys = spendKeys(h.clock.ms);
    const reserved = [...fa.aws.table.items.entries()].filter(([k, i]) => k.startsWith("billing#") && k !== BILLING_PAUSE_KEY && (i.state as { S: string }).S === "reserved");
    const ttlDays = (Number((reserved[0]![1].ttl as { N: string }).N) - Math.floor(h.clock.ms / 1000)) / 86400;
    console.log(`D2 ${where}: pause=${fa.aws.table.items.has(BILLING_PAUSE_KEY)} debts=${fa.items("billingdebt#").length} reservedEvents=${reserved.length} eventTtlDays=${ttlDays} month=${fa.aws.table.num(keys.month, "m")} logLines=${h.logs.length}`);
    expect(fa.aws.table.items.has(BILLING_PAUSE_KEY)).toBe(false);
    expect(fa.items("billingdebt#")).toHaveLength(0);
    expect(h.logs).toHaveLength(0); // no app log line -> BillingAnomaly metric filter never sees it
    // A fresh instance (the runtime replaces the killed one) proceeds to the model.
    fa.fault = undefined;
    fa.aws.model = () => ({ status: 200, json: modelReply() });
    const fresh = harness({ transport: fa.transport });
    const r = await fresh.handler(evalEvent()) as EvaluationResult;
    console.log(`   fresh instance: status=${r.status} modelCalled=${r.evaluation.modelCalled}`);
    expect(r.evaluation.modelCalled).toBe(true);
    expect(fa.aws.modelCalls).toHaveLength(2);
  });
});
