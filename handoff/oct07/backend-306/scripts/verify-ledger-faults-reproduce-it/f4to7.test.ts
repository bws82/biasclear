import { describe, expect, it } from "vitest";
import { appendFileSync } from "node:fs";
import { TxDb } from "./txdb.js";
import { Ddb } from "../../pr10b-wt/packages/explain/src/aws/dynamodb.js";
import { converseModel, modelRequest } from "../../pr10b-wt/packages/explain/src/aws/bedrock.js";
import { reserve, BILLING_PAUSE_KEY, spendKeys } from "../../pr10b-wt/packages/explain/src/spend.js";
import { config, harness, httpEvent, modelReply, STUB_MODELS, FakeAws } from "../../pr10b-wt/packages/explain/test/helpers.js";

const out = (tag: string, o: unknown) => appendFileSync(import.meta.dirname + "/results.txt", `### ${tag} ${JSON.stringify(o)}\n`);
const lastJson = (logs: string[]) => JSON.parse(logs.at(-1)!) as Record<string, unknown>;
const isReserveTx = (b: Record<string, unknown>) => JSON.stringify(b).includes('"reserved"},"month"');
const isSettleTx = (b: Record<string, unknown>) => JSON.stringify(b).includes(":settled");
const getKey = (b: Record<string, unknown>) => (b.Key as { pk: { S: string } } | undefined)?.pk.S ?? "";
const events = (db: TxDb) => [...db.aws.table.items.entries()].filter(([k]) => k.startsWith("billing#") && k !== BILLING_PAUSE_KEY)
  .map(([, it]) => ({ s: (it.state as { S: string }).S, r: (it.reserved as { N: string }).N, a: (it.actual as { N: string } | undefined)?.N }));

describe("F4 lost reserve ack + failed readback", () => {
  it("leaks reservation; repeated leaks exhaust day cap with zero model calls", async () => {
    const db = new TxDb();
    db.hook = (op, b) => {
      if (op === "TransactWriteItems" && isReserveTx(b)) return "lost-ack";
      if (op === "GetItem" && getKey(b).startsWith("billing#") && getKey(b) !== BILLING_PAUSE_KEY) return "network";
      return undefined;
    };
    const codes: string[] = [];
    let h = harness({ transport: db.transport, env: { EXPLAIN_MONTHLY_CAP_USD: "1", EXPLAIN_DAILY_PERCENT: "25" } });
    const keys = spendKeys(h.clock.ms);
    for (let i = 0; i < 40; i++) {
      if (i % 9 === 0) h = harness({ transport: db.transport, env: { EXPLAIN_MONTHLY_CAP_USD: "1", EXPLAIN_DAILY_PERCENT: "25" } });
      await h.call(httpEvent({ ip: `198.51.100.${10 + i}` }));
      codes.push(lastJson(h.logs).code as string);
      if (codes.at(-1) !== "E_DDB") break;
    }
    const ev = events(db);
    out("F4", { first: codes[0], nE_DDB: codes.filter((c) => c === "E_DDB").length, last: codes.at(-1), modelCalls: db.aws.modelCalls.length,
      day: db.aws.table.num(keys.day, "m"), dailyCap: h.deps.config!.dailyMicros, reservedEvents: ev.filter((e) => e.s === "reserved").length, debts: db.keys("billingdebt#").length, pause: db.item(BILLING_PAUSE_KEY) !== undefined });
    expect(db.aws.modelCalls.length).toBe(0);
  });
});

describe("F5 debt for a committed settlement", () => {
  it("settle commits, ack lost, readback fails -> E_SETTLE debt with reserved, counters hold actual", async () => {
    const db = new TxDb();
    let settled = false;
    db.hook = (op, b) => {
      if (op === "TransactWriteItems" && isSettleTx(b)) { settled = true; return "lost-ack"; }
      if (settled && op === "GetItem" && getKey(b).startsWith("billing#") && getKey(b) !== BILLING_PAUSE_KEY) return "network";
      return undefined;
    };
    const h = harness({ transport: db.transport }); const keys = spendKeys(h.clock.ms);
    const r = await h.call(httpEvent());
    const debt = db.keys("billingdebt#")[0]?.[1];
    out("F5-ack-lost", { status: r.statusCode, code: lastJson(h.logs).code, month: db.aws.table.num(keys.month, "m"), day: db.aws.table.num(keys.day, "m"), events: events(db),
      debt: debt && { reason: (debt.reason as { S: string }).S, reserved: (debt.reserved as { N: string }).N, actual: (debt.actual as { N: string }).N } });
  });
  it("late commit after readback", async () => {
    const db = new TxDb();
    db.hook = (op, b) => (op === "TransactWriteItems" && isSettleTx(b) ? { late: 30 } : undefined);
    const h = harness({ transport: db.transport }); const keys = spendKeys(h.clock.ms);
    const r = await h.call(httpEvent());
    await new Promise((res) => setTimeout(res, 80));
    const debt = db.keys("billingdebt#")[0]?.[1];
    out("F5-late", { status: r.statusCode, code: lastJson(h.logs).code, pausePersisted: lastJson(h.logs).pausePersisted, month: db.aws.table.num(keys.month, "m"), events: events(db),
      debt: debt && { reason: (debt.reason as { S: string }).S, reserved: (debt.reserved as { N: string }).N, actual: (debt.actual as { N: string }).N } });
  });
  it("M7: bound pause committed in settle, pause readback fails -> reason overwritten to E_SETTLE", async () => {
    const db = new TxDb();
    let settled = false; let failedPauseRead = false;
    db.hook = (op, b) => {
      if (op === "TransactWriteItems" && isSettleTx(b)) { settled = true; return "lost-ack"; }
      if (settled && !failedPauseRead && op === "GetItem" && getKey(b) === BILLING_PAUSE_KEY) { failedPauseRead = true; return "network"; }
      return undefined;
    };
    db.aws.model = () => ({ status: 200, json: modelReply({ outTok: 500 }) });
    const h = harness({ transport: db.transport }); const keys = spendKeys(h.clock.ms);
    const r = await h.call(httpEvent());
    const L = lastJson(h.logs);
    out("F5-M7", { status: r.statusCode, code: L.code, billedBoundViolated: L.billedBoundViolated, overrun: L.overrun, pausePersisted: L.pausePersisted, month: db.aws.table.num(keys.month, "m"),
      events: events(db), pauseReason: (db.item(BILLING_PAUSE_KEY)?.reason as { S: string } | undefined)?.S, debtReason: (db.keys("billingdebt#")[0]?.[1].reason as { S: string } | undefined)?.S });
  });
});

describe("F6 reserve readback after definite pause cancellation", () => {
  it("API: pause present, readback throws -> DdbError (not which:pause)", async () => {
    const db = new TxDb(); const cfg = config(); const now = Date.UTC(2026, 9, 5, 14, 3, 0);
    const ddb = new Ddb(db.transport, cfg.region, cfg.table);
    db.aws.table.items.set(BILLING_PAUSE_KEY, { pk: { S: BILLING_PAUSE_KEY }, reason: { S: "E_SETTLE" } });
    db.hook = (op, b) => (op === "GetItem" && getKey(b).startsWith("billing#") && getKey(b) !== BILLING_PAUSE_KEY ? "network" : undefined);
    let res: unknown; try { res = await reserve(ddb, cfg, now, 1000); } catch (e) { res = `threw ${String(e)}`; }
    out("F6-api", { res });
  });
  it("handler: pause lands between pre-read and reserve; readback fails", async () => {
    const db = new TxDb();
    db.hook = (op, b) => {
      if (op === "TransactWriteItems" && isReserveTx(b)) { db.aws.table.items.set(BILLING_PAUSE_KEY, { pk: { S: BILLING_PAUSE_KEY }, reason: { S: "E_SETTLE" } }); }
      if (op === "GetItem" && getKey(b).startsWith("billing#") && getKey(b) !== BILLING_PAUSE_KEY) return "network";
      return undefined;
    };
    const h = harness({ transport: db.transport });
    const r = await h.call(httpEvent());
    const code1 = lastJson(h.logs).code; const pausedUntil = h.deps.state.pausedUntil;
    db.hook = undefined; h.clock.advance(1000);
    await h.call(httpEvent());
    out("F6-handler", { status: r.statusCode, code: code1, pausedUntil, modelCalls: db.aws.modelCalls.length, nextCode: lastJson(h.logs).code });
  });
});

describe("F7 cache-write pricing", () => {
  it("cacheWriteInputTokens priced at base input rate", async () => {
    const aws = new FakeAws(); const model = STUB_MODELS["us.anthropic.claude-sonnet-5-5"]!;
    aws.model = () => ({ status: 200, json: { output: { message: { role: "assistant", content: [{ text: "x" }] } }, stopReason: "end_turn", usage: { inputTokens: 10, outputTokens: 5, cacheWriteInputTokens: 300 } } });
    const o = await converseModel(aws.transport, model.region, "us." + model.foundationModelId, modelRequest("s", "u", model), model);
    out("F7", { kind: o.kind, inTok: (o as { inTok?: number }).inTok, sentBody: Object.keys(aws.modelCalls[0] ?? {}), hasCachePoint: JSON.stringify(aws.modelCalls[0]).includes("cachePoint") });
  });
});
