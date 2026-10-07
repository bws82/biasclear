// Rough frequency estimate: Poisson arrivals at the API Gateway default rate
// (2 rps), DynamoDB transactions holding their items ~20 ms, model 1-6 s.
// Time is scaled 1 real ms = 20 virtual ms. Approximate (timer granularity).
import { describe, expect, it } from "vitest";
import type { EvaluationResult } from "../../pr10b-wt/packages/explain/src/app.js";
import { evalEvent, harness, modelReply } from "../../pr10b-wt/packages/explain/test/helpers.js";
import { FaultAws, rng, sleep } from "./faultdb.js";

const SCALE = 20;

describe("S1: requests until ordinary contention first writes a durable pause", () => {
  it("2 rps, 20 ms transactions", async () => {
    const rows: string[] = [];
    for (const seed of [11, 12, 13, 14]) {
      const fa = new FaultAws();
      fa.txMs = 20 / SCALE;
      const rand = rng(seed);
      fa.aws.model = async () => { await sleep((1000 + rand() * 5000) / SCALE); return { status: 200, json: modelReply() }; };
      const pool = Array.from({ length: 16 }, () => harness({ transport: fa.transport }));
      const inflight: Promise<EvaluationResult>[] = [];
      let firstSettle = -1, firstDdb = -1, sent = 0;
      const codes: Record<string, number> = {};
      for (let i = 0; i < 300 && firstSettle < 0; i++) {
        await sleep((-Math.log(1 - rand()) * 500) / SCALE); // mean 500 ms between arrivals
        const idx = i;
        sent++;
        inflight.push((pool[i % pool.length]!.handler(evalEvent()) as Promise<EvaluationResult>).then((r) => {
          const c = r.evaluation.code ?? "ok";
          codes[c] = (codes[c] ?? 0) + 1;
          if (c === "E_SETTLE" && firstSettle < 0) firstSettle = idx;
          if (c === "E_DDB" && firstDdb < 0) firstDdb = idx;
          return r;
        }));
      }
      await Promise.all(inflight);
      const events = fa.items("billing#").filter(([k]) => k !== "billing#pause").length;
      console.log("INV modelCalls", fa.aws.modelCalls.length, "<= committed reservation events", events);
      expect(fa.aws.modelCalls.length).toBeLessThanOrEqual(events);
      rows.push(`seed ${seed}: sent=${sent} conflicts=${fa.conflicts} firstE_DDB=#${firstDdb} firstE_SETTLE(durable pause)=#${firstSettle} codes=${JSON.stringify(codes)}`);
    }
    console.log("S1\n" + rows.join("\n"));
    expect(rows.length).toBe(4);
  });
});
