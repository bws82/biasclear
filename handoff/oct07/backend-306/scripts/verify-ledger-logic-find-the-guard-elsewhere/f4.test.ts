import { expect, it } from "vitest";
import { spendKeys } from "../../pr10b-wt/packages/explain/src/spend.js";
import { evalEvent, harness, lastLog, modelReply } from "../../pr10b-wt/packages/explain/test/helpers.js";

for (const K of [1, 3]) it(`F4 K=${K} in-flight breaches before detection`, async () => {
  const h = harness();
  const keys = spendKeys(h.clock.ms);
  const R = 9205;
  h.aws.table.items.set(keys.month, { pk: { S: keys.month }, m: { N: String(25_000_000 - K * R) } });
  let release!: () => void; const all = new Promise<void>((r) => { release = r; });
  h.aws.model = async () => {
    if (h.aws.modelCalls.length >= K) release();
    await all;
    return { status: 200, json: modelReply({ inTok: 820, outTok: 128_000 }) };
  };
  const ps = Array.from({ length: K }, () => h.handler(evalEvent()));
  await Promise.all(ps);
  const after = await h.handler(evalEvent());
  const month = h.aws.table.num(keys.month, "m")!;
  console.log(`F4 K=${K}`, { reservedEach: JSON.parse(h.logs[0]!).reservedMicros, codes: h.logs.map((l) => JSON.parse(l).code),
    modelCalls: h.aws.modelCalls.length, monthUsd: month / 1e6, nextCode: lastLog(h).code });
  expect(h.aws.modelCalls.length).toBe(K);
});
