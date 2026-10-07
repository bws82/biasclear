import { expect, it } from "vitest";
import { converseModel, modelRequest } from "../../pr10b-wt/packages/explain/src/aws/bedrock.js";
import { actualMicros } from "../../pr10b-wt/packages/explain/src/spend.js";
import { STUB_MODELS, config } from "../../pr10b-wt/packages/explain/test/helpers.js";
it("F9: cacheWriteInputTokens are priced at 1x input", async () => {
  const id = "us.anthropic.claude-sonnet-5-5"; const m = STUB_MODELS[id]!;
  const body = { output: { message: { role: "assistant", content: [{ text: "x" }] } }, stopReason: "end_turn",
    usage: { inputTokens: 100, outputTokens: 50, cacheWriteInputTokens: 2000, totalTokens: 2150 } };
  const o = await converseModel(async () => ({ status: 200, headers: {}, body: JSON.stringify(body) }), m.region, id, modelRequest("s", "u", m), m);
  const cfg = config({ EXPLAIN_MODEL_ID: id, EXPLAIN_PRICE_OUT: "11" });
  if (o.kind !== "reply") throw new Error(o.kind);
  const charged = actualMicros(o.inTok, o.outTok, cfg);
  const at125 = Math.ceil((100 * 2200 + 2000 * 2200 * 1.25 + 50 * 11000) / 1000);
  console.log({ inTok: o.inTok, charged, ifCacheWriteIs1_25x: at125 });
  expect(charged).toBeLessThan(at125);
});
