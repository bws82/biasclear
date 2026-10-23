// find-the-guard-elsewhere: with ONE invocation at a time per instance (standard
// Lambda, no capacity provider in explain.yaml), can a failed privacy verdict or
// an in-memory Infinity stop ever be bypassed? Seeded sequential fuzz.
import { describe, expect, it } from "vitest";
import { harness, httpEvent, modelReply } from "../../pr10b-wt/packages/explain/test/helpers.js";
import { MODELS, modelReady } from "../../pr10b-wt/packages/explain/src/models.js";
import { readConfig } from "../../pr10b-wt/packages/explain/src/config.js";
import { SETTINGS_INTERVAL_MS } from "../../pr10b-wt/packages/explain/src/state.js";

function rng(seed: number) { return () => { seed = (seed * 1103515245 + 12345) & 0x7fffffff; return seed / 0x7fffffff; }; }

describe("production table at this head", () => {
  it("every reviewed model is not ready, so readConfig refuses (E_CONFIG before step 2)", () => {
    for (const [id, m] of Object.entries(MODELS)) {
      expect(modelReady(m), id).toBe(false);
      expect(readConfig({ EXPLAIN_SWITCH: "on", AWS_REGION: "us-east-1", EXPLAIN_TABLE: "biasclear-explain", EXPLAIN_MODEL_ID: id,
        EXPLAIN_PRICE_IN: String(m.inputPricePerMillion), EXPLAIN_PRICE_OUT: String(m.outputPricePerMillion), EXPLAIN_MONTHLY_CAP_USD: "5",
        EXPLAIN_DAILY_PERCENT: "10", EXPLAIN_ORIGINS: "https://biasclear.com", EXPLAIN_RETENTION_MODE: "none", EXPLAIN_RATE_10MIN: "5", EXPLAIN_RATE_DAY: "20" }), id).toBeUndefined();
    }
  });
});

describe("sequential invocations only", () => {
  it("no model call follows a failed privacy verdict without a fresh passing read; Infinity never lowered", async () => {
    let totalReq = 0, totalModel = 0, fails = 0, lowered = 0;
    for (let seed = 1; seed <= 300; seed++) {
      const r = rng(seed);
      const h = harness();
      let tainted = false; // last verdict was a failure
      let ipn = 0;
      for (let step = 0; step < 60; step++) {
        const a = r();
        if (a < 0.15) h.aws.settings = { logging: { cloudWatchConfig: { logGroupName: "x" } }, retention: "none" };
        else if (a < 0.30) h.aws.settings = { logging: {}, retention: "none" };
        else if (a < 0.35) h.aws.settings = "fail";
        const m = r();
        h.aws.model = m < 0.6 ? () => ({ status: 200, json: modelReply() })
          : m < 0.8 ? () => ({ status: 403, errorType: "AccessDeniedException", json: { message: "d" } })
          : m < 0.95 ? () => ({ status: 429, errorType: "ThrottlingException", json: { message: "t" } })
          : () => "timeout";
        if (r() < 0.1) for (const [k, v] of h.aws.table.items) if (k.startsWith("spendday#")) h.aws.table.items.set(k, { ...v, m: { N: String(h.deps.config!.dailyMicros) } });
        const adv = r();
        h.clock.advance(adv < 0.4 ? Math.floor(r() * 60_000) : adv < 0.8 ? Math.floor(r() * SETTINGS_INTERVAL_MS * 1.2) : Math.floor(r() * 26 * 3600_000));
        const wasInf = h.deps.state.pausedUntil === Number.POSITIVE_INFINITY;
        const reads0 = h.aws.settingsReads, models0 = h.aws.modelCalls.length;
        await h.call(httpEvent({ ip: `198.51.${100 + (ipn >> 8)}.${(ipn++ & 255) || 1}` }));
        totalReq++;
        const code = (JSON.parse(h.logs.at(-1)!) as { code?: string }).code;
        const freshRead = h.aws.settingsReads > reads0;
        const settingsFail = code !== undefined && code.startsWith("E_SETTINGS_");
        if (h.aws.modelCalls.length > models0) {
          totalModel++;
          // a model call is allowed only after a passing verdict (fresh in this request, or the last one recorded)
          expect(freshRead || !tainted, `seed ${seed} step ${step}`).toBe(true);
        }
        if (freshRead) { tainted = settingsFail; if (settingsFail) fails++; }
        if (wasInf && h.deps.state.pausedUntil !== Number.POSITIVE_INFINITY) lowered++;
        expect(wasInf && h.deps.state.pausedUntil !== Number.POSITIVE_INFINITY, `seed ${seed} step ${step} lowered Infinity`).toBe(false);
      }
    }
    console.log(JSON.stringify({ totalReq, totalModel, fails, lowered }));
    expect(fails).toBeGreaterThan(50);
    expect(totalModel).toBeGreaterThan(50);
  });
});
