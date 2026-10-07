import { describe, expect, it } from "vitest";
import { TxDb, sleep } from "./txdb.js";
import { Ddb } from "../../pr10b-wt/packages/explain/src/aws/dynamodb.js";
import { reserve, persistBillingPause, BILLING_PAUSE_KEY, spendKeys } from "../../pr10b-wt/packages/explain/src/spend.js";
import { config, harness, httpEvent, modelReply } from "../../pr10b-wt/packages/explain/test/helpers.js";

const cfg = config();
const now = Date.UTC(2026, 9, 5, 14, 3, 0);
import { appendFileSync } from "node:fs";
const out = (tag: string, o: unknown) => appendFileSync(import.meta.dirname + "/results.txt", `### ${tag} ${JSON.stringify(o)}\n`);
const lastJson = (logs: string[]) => JSON.parse(logs.at(-1)!) as Record<string, unknown>;

describe("F1 persistBillingPause vs concurrent reserve", () => {
  it("API: persist while another reserve holds billing#pause", async () => {
    const db = new TxDb(); const ddb = new Ddb(db.transport, cfg.region, cfg.table);
    const a = await reserve(ddb, cfg, now, 10000); if (!a.ok) throw new Error("x");
    db.holdMs = 40;
    const bP = reserve(ddb, cfg, now, 10000);
    while (!db.held.has(BILLING_PAUSE_KEY)) await sleep(1);
    const persisted = await persistBillingPause(ddb, { reason: "E_MODEL_NO_USAGE", nowMs: now, reservedMicros: 10000, event: a.reservation.event });
    const b = await bP;
    const r = { persisted, bOk: b.ok, pause: db.item(BILLING_PAUSE_KEY) !== undefined, debts: db.keys("billingdebt#").length, log: db.log };
    out("F1-api", r);
    expect(persisted).toBe(false); expect(r.pause).toBe(false); expect(r.debts).toBe(0); expect(b.ok).toBe(true);
  });
  it("API reverse order: reserve arrives during persist -> reserve cancelled, persist ok", async () => {
    const db = new TxDb(); const ddb = new Ddb(db.transport, cfg.region, cfg.table);
    const a = await reserve(ddb, cfg, now, 10000); if (!a.ok) throw new Error("x");
    db.holdMs = 40;
    const pP = persistBillingPause(ddb, { reason: "E_MODEL_NO_USAGE", nowMs: now, reservedMicros: 10000, event: a.reservation.event });
    while (!db.held.has(BILLING_PAUSE_KEY)) await sleep(1);
    let bres: unknown; try { bres = await reserve(ddb, cfg, now, 10000); } catch (e) { bres = String(e); }
    const persisted = await pP;
    out("F1-api-rev", { persisted, bres, debts: db.keys("billingdebt#").length });
  });
  it("API: two concurrent persists", async () => {
    const db = new TxDb(); const ddb = new Ddb(db.transport, cfg.region, cfg.table);
    const a = await reserve(ddb, cfg, now, 10000); const b = await reserve(ddb, cfg, now, 10000);
    if (!a.ok || !b.ok) throw new Error("x");
    db.holdMs = 40;
    const res = await Promise.all([a, b].map((x, i) => persistBillingPause(ddb, { reason: "E_SETTLE", nowMs: now, reservedMicros: 10000, actualMicros: 15000 + i, event: (x as { reservation: { event: string } }).reservation.event })));
    out("F1-c4", { res, debts: db.keys("billingdebt#").map(([, it]) => (it.actual as { N: string }).N), pause: db.item(BILLING_PAUSE_KEY) !== undefined });
    expect(res.filter(Boolean)).toHaveLength(1);
  });
  it("handler: A maybe-billed while B reserves; fresh C keeps calling", async () => {
    const db = new TxDb();
    const hA = harness({ transport: db.transport }); const hB = harness({ transport: db.transport }); const hC = harness({ transport: db.transport });
    let n = 0; let bP: Promise<unknown> | undefined;
    db.aws.model = async () => {
      n++;
      if (n === 1) {
        bP = hB.call(httpEvent({ ip: "198.51.100.2" }));
        while (!db.held.has(BILLING_PAUSE_KEY)) await sleep(1);
        return { status: 200, json: modelReply({ usage: null }) };
      }
      return { status: 200, json: modelReply() };
    };
    db.holdMs = 40;
    const ra = await hA.call(httpEvent({ ip: "198.51.100.1" }));
    const rb = (await bP) as { statusCode: number };
    const rc = await hC.call(httpEvent({ ip: "198.51.100.3" }));
    const r = { a: ra.statusCode, aLog: lastJson(hA.logs), b: rb.statusCode, c: rc.statusCode, modelCalls: db.aws.modelCalls.length,
      pause: db.item(BILLING_PAUSE_KEY) !== undefined, debts: db.keys("billingdebt#").length, conflicts: db.log };
    out("F1-handler", r);
    expect(r.aLog.pausePersisted).toBe(0); expect(r.c).toBe(200); expect(r.pause).toBe(false);
  });
});

describe("F2 settle cancelled by a concurrent reserve", () => {
  for (const variant of ["natural", "B-done-before-persist"] as const) {
    it(`handler: ${variant}`, async () => {
      const db = new TxDb();
      const hA = harness({ transport: db.transport }); const hB = harness({ transport: db.transport }); const hC = harness({ transport: db.transport });
      const keys = spendKeys(hA.clock.ms);
      let n = 0; let bP: Promise<unknown> | undefined;
      db.aws.model = async () => {
        n++;
        if (n === 1) {
          bP = hB.call(httpEvent({ ip: "198.51.100.2" }));
          while (!db.held.has(keys.month)) await sleep(1);
          return { status: 200, json: modelReply() };
        }
        return { status: 200, json: modelReply() };
      };
      if (variant === "B-done-before-persist") {
        db.hook = async (op, _b, k) => {
          if (op === "TransactWriteItems" && k[0] === BILLING_PAUSE_KEY && k.length === 2) { while (db.held.size) await sleep(1); }
          return undefined;
        };
      }
      db.holdMs = 40;
      const ra = await hA.call(httpEvent({ ip: "198.51.100.1" }));
      const rb = (await bP) as { statusCode: number };
      const rc = await hC.call(httpEvent({ ip: "198.51.100.3" }));
      const aLog = lastJson(hA.logs);
      const ev = [...db.aws.table.items.entries()].filter(([k]) => k.startsWith("billing#") && k !== BILLING_PAUSE_KEY).map(([, it]) => ({ s: (it.state as { S: string }).S, r: (it.reserved as { N: string }).N, a: (it.actual as { N: string } | undefined)?.N }));
      const r = { a: ra.statusCode, aBody: ra.json, aLog, b: rb.statusCode, c: rc.statusCode, cLog: lastJson(hC.logs), month: db.aws.table.num(keys.month, "m"),
        events: ev, pause: db.item(BILLING_PAUSE_KEY)?.reason, debts: db.keys("billingdebt#").length, conflicts: db.log };
      out(`F2-${variant}`, r);
      expect(aLog.code).toBe("E_SETTLE");
    });
  }
});
