// Independent checks (not using the red-team's FaultAws): wrap the package FakeAws
// transport and return DynamoDB's documented TransactionCanceledException shapes.
import { describe, expect, it } from "vitest";
import type { EvaluationResult } from "../../pr10b-wt/packages/explain/src/app.js";
import type { AwsCall, Transport } from "../../pr10b-wt/packages/explain/src/aws/transport.js";
import { Ddb } from "../../pr10b-wt/packages/explain/src/aws/dynamodb.js";
import { BILLING_PAUSE_KEY, persistBillingPause, reserve, spendKeys } from "../../pr10b-wt/packages/explain/src/spend.js";
import { FakeAws, config, evalEvent, harness, httpEvent, lastLog, modelReply } from "../../pr10b-wt/packages/explain/test/helpers.js";

const cfg = config();
const now = Date.UTC(2026, 9, 7, 14);
const cancelled = (n: number, at: number, code: string) => ({
  status: 400, headers: {},
  body: JSON.stringify({ __type: "com.amazonaws.dynamodb.v20120810#TransactionCanceledException",
    CancellationReasons: Array.from({ length: n }, (_, i) => ({ Code: i === at ? code : "None" })) }),
});
const isTx = (c: AwsCall) => c.service === "dynamodb" && (c.headers["x-amz-target"] ?? "").endsWith("TransactWriteItems");
const items = (c: AwsCall) => (JSON.parse(c.body).TransactItems as unknown[]).length;

describe("G1 persist: one cancellation of the pause item drops the uncontended debt too", () => {
  for (const code of ["TransactionConflict", "ThrottlingError"]) it(code, async () => {
    const aws = new FakeAws();
    const t: Transport = async (c) => (isTx(c) && !c.body.includes("ConditionCheck") && c.body.includes("billingdebt#") ? cancelled(items(c), 0, code) : aws.transport(c));
    const ddb = new Ddb(t, cfg.region, cfg.table);
    const r = await reserve(ddb, cfg, now, 10_000); if (!r.ok) throw new Error("x");
    const ok = await persistBillingPause(ddb, { reason: "E_MODEL_TIMEOUT", nowMs: now, reservedMicros: 10_000, event: r.reservation.event });
    const debts = [...aws.table.items.keys()].filter((k) => k.startsWith("billingdebt#"));
    console.log("G1", code, "persisted", ok, "pause", aws.table.items.has(BILLING_PAUSE_KEY), "debts", debts.length,
      "event state", JSON.stringify(aws.table.items.get(r.reservation.event)?.state), "eventTtl?", aws.table.items.get(r.reservation.event)?.ttl !== undefined);
    expect(ok).toBe(false);
    expect(debts).toHaveLength(0);
  });

  it("handler: maybe-billed + persist conflict -> only this instance fenced; fresh instance calls the model; log line still emitted", async () => {
    const aws = new FakeAws();
    let conflictPersist = true;
    const t: Transport = async (c) => (conflictPersist && isTx(c) && c.body.includes("billingdebt#") ? cancelled(items(c), 0, "TransactionConflict") : aws.transport(c));
    aws.model = () => ({ status: 200, json: modelReply({ usage: null }) });
    const a = harness({ transport: t });
    const ra = await a.handler(evalEvent()) as EvaluationResult;
    console.log("G1h A", ra.status, ra.evaluation.code, "pausePersisted", ra.evaluation.pausePersisted, "log", JSON.stringify(lastLog(a)));
    expect(ra.evaluation.pausePersisted).toBe(false);
    expect(lastLog(a).pausePersisted).toBe(0); // the metric filter sees this line
    expect((await a.call(httpEvent())).statusCode).toBe(503); // instance fenced in memory
    conflictPersist = false;
    aws.model = () => ({ status: 200, json: modelReply() });
    const b = harness({ transport: t });
    const rb = await b.handler(evalEvent()) as EvaluationResult;
    console.log("G1h fresh", rb.status, "modelCalled", rb.evaluation.modelCalled);
    expect(rb.evaluation.modelCalled).toBe(true);
  });
});

describe("G2 settle: a definite TransactionConflict cancellation is handled as uncertain", () => {
  for (const code of ["TransactionConflict", "ThrottlingError"]) it(code, async () => {
    const aws = new FakeAws();
    let once = true;
    const t: Transport = async (c) => {
      if (once && isTx(c) && c.body.includes(":settled")) { once = false; return cancelled(items(c), 1, code); }
      return aws.transport(c);
    };
    const h = harness({ transport: t });
    const r = await h.handler(evalEvent()) as EvaluationResult;
    const keys = spendKeys(h.clock.ms);
    console.log("G2", code, r.status, r.evaluation.code, "pausePersisted", r.evaluation.pausePersisted, "month", aws.table.num(keys.month, "m"), "reserved", r.evaluation.reservedMicros, "actual", r.evaluation.actualMicros);
    expect(r.evaluation.code).toBe("E_SETTLE");
    expect(aws.table.items.has(BILLING_PAUSE_KEY)).toBe(true);
    const fresh = harness({ transport: t });
    expect((await fresh.call(httpEvent())).statusCode).toBe(503);
    expect(lastLog(fresh).code).toBe("E_BILLING_PAUSE");
  });
});

describe("G3 not-billed release conflict also pauses durably", () => {
  it("release cancelled -> E_SETTLE durable pause", async () => {
    const aws = new FakeAws();
    aws.model = () => ({ status: 429, json: { message: "Too many requests" }, errorType: "ThrottlingException" });
    let once = true;
    const t: Transport = async (c) => {
      if (once && isTx(c) && c.body.includes(":settled")) { once = false; return cancelled(items(c), 1, "TransactionConflict"); }
      return aws.transport(c);
    };
    const h = harness({ transport: t });
    const r = await h.handler(evalEvent()) as EvaluationResult;
    console.log("G3", r.status, r.evaluation.code, "modelCalled", r.evaluation.modelCalled, "pause", aws.table.items.has(BILLING_PAUSE_KEY));
  });
});
