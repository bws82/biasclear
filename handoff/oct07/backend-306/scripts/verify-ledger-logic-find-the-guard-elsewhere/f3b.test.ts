import { expect, it } from "vitest";
import { TransportError, type Transport } from "../../pr10b-wt/packages/explain/src/aws/transport.js";
import { FakeAws, evalEvent, harness, lastLog, modelReply } from "../../pr10b-wt/packages/explain/test/helpers.js";

// Count sequential DynamoDB calls after the model when the first post-model transaction
// times out (not applied) and every later call is slow-but-answered (each may take up to 3 s).
async function chain(model: FakeAws["model"], failFirstTx: boolean, preModelCount = false) {
  const aws = new FakeAws(); aws.model = model;
  let after = false; let n = 0; let pre = 0; let failed = false;
  const t: Transport = async (call) => {
    if (call.host.startsWith("bedrock-runtime.")) { try { return await aws.transport(call); } finally { after = true; } }
    if (call.service === "dynamodb") {
      if (!after) { pre++; return aws.transport(call); }
      n++;
      const op = (call.headers["x-amz-target"] ?? "");
      if (failFirstTx && !failed && op.endsWith("TransactWriteItems")) { failed = true; throw new TransportError("timeout"); }
    }
    return aws.transport(call);
  };
  const h = harness({ transport: t });
  await h.handler(evalEvent());
  return { pre, n, code: lastLog(h).code, pausePersisted: lastLog(h).pausePersisted };
}
it("F3 chain lengths", async () => {
  const breach = await chain(() => ({ status: 200, json: modelReply({ inTok: 300, outTok: 30_000 }) }), true);
  const okSettleFail = await chain(() => ({ status: 200, json: modelReply() }), true);
  const unknownSlow = await chain(() => "timeout", false);
  const unknownTxFail = await chain(() => "timeout", true);
  console.log("F3b", { breach, okSettleFail, unknownSlow, unknownTxFail });
  console.log("worst ms (20 s model + n x 3 s):", { breach: 20000 + breach.n * 3000, unknownTxFail: 20000 + unknownTxFail.n * 3000, unknownSlow: 20000 + unknownSlow.n * 3000 });
  expect(breach.n).toBeGreaterThanOrEqual(4);
});
