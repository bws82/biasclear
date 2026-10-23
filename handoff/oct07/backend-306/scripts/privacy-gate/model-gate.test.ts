// Q2: config/model-table gating. Can unverified evidence reach Bedrock?
import { describe, expect, it } from "vitest";
import { createHandler } from "../../pr10b-wt/packages/explain/src/app.js";
import { converseModel, modelRequest } from "../../pr10b-wt/packages/explain/src/aws/bedrock.js";
import { readConfig } from "../../pr10b-wt/packages/explain/src/config.js";
import { MODELS, modelReady, type ModelInfo } from "../../pr10b-wt/packages/explain/src/models.js";
import { bundledEngines } from "../../pr10b-wt/packages/explain/src/engines.js";
import { bundledMoves } from "../../pr10b-wt/packages/explain/src/moves.js";
import { newState } from "../../pr10b-wt/packages/explain/src/state.js";
import { ENV, FakeAws, STUB_MODELS, evalEvent, httpEvent, stubConfig } from "../../pr10b-wt/packages/explain/test/helpers.js";

const PRICES: Record<string, [string, string]> = {
  "us.xai.grok-4.7": ["2.2", "6.6"],
  "us.anthropic.claude-sonnet-5-5": ["2.2", "11"],
  "us.openai.gpt-6.1-sol": ["2.2", "11"],
};

function prodHandler(env: Record<string, string>, configOverride?: ReturnType<typeof readConfig>) {
  const aws = new FakeAws();
  const logs: string[] = [];
  const handler = createHandler({
    config: configOverride === undefined ? readConfig(env) : configOverride,
    transport: aws.transport, now: () => Date.UTC(2026, 9, 7, 12), randomBytes: (n) => new Uint8Array(n),
    engines: bundledEngines(), moves: bundledMoves(), promptMode: "how-and-plainer",
    sink: (l) => logs.push(l), state: newState(),
  });
  return { aws, logs, handler };
}

describe("production MODELS (no injection) never reach any AWS call", () => {
  for (const [id, [pin, pout]] of Object.entries(PRICES)) {
    it(`${id}: readConfig refuses; HTTP and evaluation events answer paused with zero AWS calls`, async () => {
      const env = { ...ENV, EXPLAIN_MODEL_ID: id, EXPLAIN_PRICE_IN: pin, EXPLAIN_PRICE_OUT: pout };
      expect(readConfig(env)).toBeUndefined();
      expect(modelReady(MODELS[id])).toBe(false);
      expect(stubConfig(env)).toBeDefined(); // the same env is otherwise valid
      const p = prodHandler(env);
      for (const ev of [httpEvent(), evalEvent()]) await p.handler(ev);
      expect(p.aws.calls).toEqual([]);
      expect(p.logs.map((l) => JSON.parse(l).code)).toEqual(["E_CONFIG", "E_EVAL_KEY"]);
    });
  }

  it("a Config minted from a synthetic ready table is still refused by app.ts against the production table", async () => {
    const env = { ...ENV };
    const cfg = stubConfig(env)!;
    const p = prodHandler(env, cfg);
    await p.handler(httpEvent());
    await p.handler(evalEvent());
    expect(p.aws.calls).toEqual([]);
    expect(p.logs.map((l) => JSON.parse(l).code)).toEqual(["E_CONFIG", "E_CONFIG"]);
  });

  it("converseModel refuses every production row before the transport", async () => {
    const aws = new FakeAws();
    for (const [id, m] of Object.entries(MODELS)) {
      const r = await converseModel(aws.transport, "us-east-1", id, modelRequest("s", "u", m));
      expect(r).toMatchObject({ modelCalled: false, kind: "not-billed", code: "E_CONFIG" });
    }
    expect(aws.calls).toEqual([]);
  });
});

describe("modelReady requires every evidence field", () => {
  const base = STUB_MODELS["us.xai.grok-4.7"]!;
  const mutations: Array<[string, Partial<ModelInfo> | ((m: ModelInfo) => ModelInfo)]> = [
    ["liveBlockReason non-empty", { liveBlockReason: "x" }],
    ["liveBlockReason whitespace", { liveBlockReason: " " }],
    ["settingsVerified false", { settingsVerified: false }],
    ["reasoningAccounting unknown", (m) => ({ ...m, reasoningAccounting: { ...m.reasoningAccounting, state: "unknown" } })],
    ["reasoningAccounting no", (m) => ({ ...m, reasoningAccounting: { ...m.reasoningAccounting, state: "no" } })],
    ["inputTokenBound unknown", (m) => ({ ...m, inputTokenBound: { ...m.inputTokenBound, state: "unknown" } })],
    ["framingTokens null", (m) => ({ ...m, inputTokenBound: { ...m.inputTokenBound, framingTokens: null } })],
    ["framingTokens negative", (m) => ({ ...m, inputTokenBound: { ...m.inputTokenBound, framingTokens: -1 } })],
    ["framingTokens fractional", (m) => ({ ...m, inputTokenBound: { ...m.inputTokenBound, framingTokens: 1.5 } })],
    ["framingTokens NaN", (m) => ({ ...m, inputTokenBound: { ...m.inputTokenBound, framingTokens: Number.NaN } })],
    ["billedMaxTokens null", { billedMaxTokens: null }],
    ["billedMaxTokens < maxTokens", { billedMaxTokens: 399 }],
    ["billedMaxTokens Infinity", { billedMaxTokens: Number.POSITIVE_INFINITY }],
    ["billedMaxTokens string", { billedMaxTokens: "400" as unknown as number }],
  ];
  it("base synthetic row is ready", () => expect(modelReady(base)).toBe(true));
  for (const [name, mut] of mutations) {
    it(`blocks: ${name}`, () => {
      const m = typeof mut === "function" ? mut(base) : { ...base, ...mut };
      expect(modelReady(m as ModelInfo)).toBe(false);
    });
  }
  it("(observation) modelReady itself does not check route/region/destinations/requestFields; readConfig + app + converseModel do", () => {
    const m = { ...base, route: "global-profile", destinationRegions: [], requestFields: { tools: [{}] } } as unknown as ModelInfo;
    expect(modelReady(m)).toBe(true);
    const models = { "us.xai.grok-4.7": m };
    expect(readConfig(ENV, models)).toBeUndefined(); // route !== us-profile
    const m2 = { ...base, destinationRegions: [] } as unknown as ModelInfo;
    expect(readConfig(ENV, { "us.xai.grok-4.7": m2 })).toBeDefined(); // empty destinations accepted at runtime
  });
});
