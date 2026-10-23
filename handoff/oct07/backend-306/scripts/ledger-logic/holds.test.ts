// Checks of claims that should hold.
import { describe, expect, it } from "vitest";
import { Ddb } from "../../pr10b-wt/packages/explain/src/aws/dynamodb.js";
import { actualMicros, hasHeadroom, release, reserve, settle, spendKeys, worstCaseMicros } from "../../pr10b-wt/packages/explain/src/spend.js";
import { FakeAws, config } from "../../pr10b-wt/packages/explain/test/helpers.js";

describe("holds", () => {
  it("rounding: any in-bound usage costs at most the reservation (200k random cases, all price pairs in the table)", () => {
    let seed = 12345;
    const rnd = (n: number) => { seed = (seed * 1103515245 + 12345) % 2 ** 31; return seed % n; };
    for (const prices of [{ inNanosPerToken: 2200, outNanosPerToken: 6600 }, { inNanosPerToken: 2200, outNanosPerToken: 11000 }, { inNanosPerToken: 1, outNanosPerToken: 1 }, { inNanosPerToken: 999, outNanosPerToken: 1001 }]) {
      for (let i = 0; i < 50_000; i++) {
        const bytes = rnd(4096), framing = rnd(200), maxT = 1 + rnd(2000);
        const w = worstCaseMicros(bytes, maxT, prices, framing);
        const inTok = rnd(bytes + framing + 1), outTok = rnd(maxT + 1);
        expect(actualMicros(inTok, outTok, prices)).toBeLessThanOrEqual(w);
      }
    }
  });

  it("month boundary is exact (no off-by-one) and an over-cap counter refuses everything", async () => {
    const aws = new FakeAws(); const cfg = config();
    const ddb = new Ddb(aws.transport, cfg.region, cfg.table);
    const now = Date.UTC(2026, 9, 20, 12);
    const k = spendKeys(now);
    aws.table.items.set(k.month, { pk: { S: k.month }, m: { N: String(cfg.capMicros - 1000) } });
    expect(await hasHeadroom(ddb, cfg, now, 1001)).toBe(false);
    expect(await reserve(ddb, cfg, now, 1001)).toEqual({ ok: false, which: "month" });
    const r = await reserve(ddb, cfg, now, 1000);
    expect(r.ok).toBe(true);
    if (!r.ok) return;
    expect(await settle(ddb, r.reservation, 5000)).toBe(true); // overrun pushes counter above cap
    expect(aws.table.num(k.month, "m")).toBe(cfg.capMicros + 4000);
    expect(await reserve(ddb, cfg, now, 1)).toEqual({ ok: false, which: "month" });
    // A duplicate release after settlement subtracts nothing.
    expect(await release(ddb, r.reservation)).toBe(false);
    expect(aws.table.num(k.month, "m")).toBe(cfg.capMicros + 4000);
  });

  it("event ids and settle tokens are distinct", async () => {
    const aws = new FakeAws(); const cfg = config();
    const ddb = new Ddb(aws.transport, cfg.region, cfg.table);
    const tokens: string[] = [];
    const inner = aws.transport;
    const ddb2 = new Ddb(async (c) => { const b = JSON.parse(c.body) as { ClientRequestToken?: string }; if (b.ClientRequestToken) tokens.push(b.ClientRequestToken); return inner(c); }, cfg.region, cfg.table);
    void ddb;
    const now = Date.UTC(2026, 9, 20, 12);
    const seen = new Set<string>();
    for (let i = 0; i < 300; i++) {
      const r = await reserve(ddb2, cfg, now, 10); if (!r.ok) throw new Error("x");
      expect(seen.has(r.reservation.event)).toBe(false); seen.add(r.reservation.event);
      expect(r.reservation.event).not.toBe("billing#pause");
      await settle(ddb2, r.reservation, 5);
    }
    expect(new Set(tokens).size).toBe(tokens.length);
  });
});
