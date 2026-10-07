// F3: the code's own per-call timeouts do not fit inside the 28 s Lambda Timeout
// (infra/aws/explain.yaml:208). Virtual clock only; no real waiting.
import { describe, expect, it } from "vitest";
import type { EvaluationResult } from "../../pr10b-wt/packages/explain/src/app.js";
import { TransportError, type AwsCall, type Transport } from "../../pr10b-wt/packages/explain/src/aws/transport.js";
import { DDB_TIMEOUT_MS } from "../../pr10b-wt/packages/explain/src/aws/dynamodb.js";
import { MODEL_TIMEOUT_MS } from "../../pr10b-wt/packages/explain/src/aws/bedrock.js";
import { BILLING_PAUSE_KEY } from "../../pr10b-wt/packages/explain/src/spend.js";
import { FakeAws, evalEvent, harness, modelReply, type Clock } from "../../pr10b-wt/packages/explain/test/helpers.js";

const LAMBDA_TIMEOUT_MS = 28_000;

type Plan = (call: AwsCall, op: string, payload: Record<string, unknown>) => { ms: number; timeout?: boolean };

function virtual(inner: Transport, clock: Clock, plan: Plan, trace: string[]): Transport {
  return async (call) => {
    const start = clock.ms;
    const op = call.service === "dynamodb" ? (call.headers["x-amz-target"] ?? "").replace("DynamoDB_20120810.", "") : call.host.startsWith("bedrock-runtime.") ? "Converse" : call.path;
    const payload = call.body ? JSON.parse(call.body) as Record<string, unknown> : {};
    const p = plan(call, op, payload);
    const tag = op === "TransactWriteItems" ? (call.body.includes("ConditionCheck") ? "reserve" : call.body.includes(":settled") ? "settle" : "persistPause") : op;
    if (p.timeout) {
      clock.ms = Math.max(clock.ms, start + p.ms);
      trace.push(`${(start / 1000 - T0 / 1000).toFixed(2)}s -> ${((start + p.ms - T0) / 1000).toFixed(2)}s ${tag} TIMEOUT`);
      throw new TransportError("timeout");
    }
    try {
      return await inner(call);
    } finally {
      clock.ms = Math.max(clock.ms, start + p.ms);
      trace.push(`${((start - T0) / 1000).toFixed(2)}s -> ${((start + p.ms - T0) / 1000).toFixed(2)}s ${tag}`);
    }
  };
}
let T0 = 0;

describe("F3: post-call accounting can run past the Lambda Timeout", () => {
  it("static budget from the code's own constants", () => {
    const postBreach = MODEL_TIMEOUT_MS + 5 * DDB_TIMEOUT_MS; // settle tx, event read, persist tx, debt read, pause read
    const postUnknown = MODEL_TIMEOUT_MS + 3 * DDB_TIMEOUT_MS; // persist tx, debt read, pause read
    console.log({ MODEL_TIMEOUT_MS, DDB_TIMEOUT_MS, LAMBDA_TIMEOUT_MS, postBreach, postUnknown });
    expect(postBreach).toBeGreaterThan(LAMBDA_TIMEOUT_MS);
    expect(postUnknown).toBeGreaterThan(LAMBDA_TIMEOUT_MS);
  });

  it("provider breach + slow DynamoDB: the durable pause/debt is only sent after 28 s", async () => {
    const aws = new FakeAws();
    const h = harness();
    T0 = h.clock.ms;
    const trace: string[] = [];
    // Breach usage: 30,000 output tokens against a 400-token bound.
    aws.model = () => ({ status: 200, json: modelReply({ inTok: 300, outTok: 30_000 }) });
    let settleSeen = false;
    h.deps.transport = virtual(aws.transport, h.clock, (_c, op, payload) => {
      if (op === "Converse") return { ms: 19_500 };
      if (op === "TransactWriteItems" && JSON.stringify(payload).includes(":settled")) { settleSeen = true; return { ms: 3_000, timeout: true }; }
      if (settleSeen) return { ms: 2_900 }; // DynamoDB stays degraded for the next calls (each < 3 s, so they succeed)
      return { ms: 40 };
    }, trace);
    const r = (await h.handler(evalEvent())) as EvaluationResult;
    const line = JSON.parse(h.logs.at(-1)!) as Record<string, unknown>;
    console.log(trace.join("\n"));
    console.log("result", r.status, line.code, "pausePersisted", line.pausePersisted, "virtual elapsed ms", line.ms);
    const persistLine = trace.find((t) => t.includes("persistPause"))!;
    const persistSentAt = Number(persistLine.split("s ->")[0]);
    console.log("persistPause sent at", persistSentAt, "s; Lambda kill at", LAMBDA_TIMEOUT_MS / 1000, "s");
    expect(line.ms as number).toBeGreaterThan(LAMBDA_TIMEOUT_MS);
    expect(aws.table.items.has(BILLING_PAUSE_KEY)).toBe(true); // only because the simulation did not kill the process
  });

  it("unknown usage (model timeout) + one failed pause write: the pausePersisted=0 log line lands after 28 s", async () => {
    const aws = new FakeAws();
    const h = harness();
    T0 = h.clock.ms;
    const trace: string[] = [];
    aws.model = () => "timeout";
    let persistSeen = false;
    h.deps.transport = virtual(aws.transport, h.clock, (_c, op, payload) => {
      if (op === "Converse") return { ms: MODEL_TIMEOUT_MS };
      if (op === "TransactWriteItems" && !JSON.stringify(payload).includes("ConditionCheck")) { persistSeen = true; return { ms: 3_000, timeout: true }; }
      if (persistSeen) return { ms: 2_900 };
      return { ms: 40 };
    }, trace);
    const r = (await h.handler(evalEvent())) as EvaluationResult;
    const line = JSON.parse(h.logs.at(-1)!) as Record<string, unknown>;
    console.log(trace.join("\n"));
    console.log("result", r.status, line.code, "pausePersisted", line.pausePersisted, "virtual elapsed ms", line.ms);
    expect(line.pausePersisted).toBe(0);
  });
});
