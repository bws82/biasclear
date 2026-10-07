// Lost/late acknowledgments, double settlement, rollover, skew, pause readback.
import { describe, expect, it } from "vitest";
import type { EvaluationResult } from "../../pr10b-wt/packages/explain/src/app.js";
import { Ddb } from "../../pr10b-wt/packages/explain/src/aws/dynamodb.js";
import { BILLING_PAUSE_KEY, persistBillingPause, release, reserve, settle, spendKeys } from "../../pr10b-wt/packages/explain/src/spend.js";
import { config, evalEvent, harness, httpEvent, lastLog, modelReply } from "../../pr10b-wt/packages/explain/test/helpers.js";
import { FaultAws, sleep } from "./faultdb.js";

const cfg = config();
const now = Date.UTC(2026, 9, 7, 14);
const isReserveTx = (op: string, b: unknown) => op === "TransactWriteItems" && JSON.stringify(b).includes("ConditionCheck");
const isSettleTx = (op: string, b: unknown) => op === "TransactWriteItems" && JSON.stringify(b).includes(":settled");

describe("M1/M2: reserve committed but unprovable", () => {
  it("M1 lost ack + failed readback: no model call, reservation leaks with no debt; leaks alone exhaust the day", async () => {
    const fa = new FaultAws();
    // Commit the reserve, then lose the reply; the consistent readback GetItem of billing#<uuid> also fails.
    fa.fault = (op, b) => isReserveTx(op, b) ? undefined : undefined;
    const inner = fa.transport;
    let leaks = 0;
    const transport: typeof inner = async (call) => {
      const body = call.body;
      if (call.service === "dynamodb" && body.includes("ConditionCheck")) { await inner(call); leaks++; throw new (await import("../../pr10b-wt/packages/explain/src/aws/transport.js")).TransportError("network"); }
      if (call.service === "dynamodb" && body.includes('"billing#') && body.includes("ConsistentRead") && !body.includes("billing#pause")) {
        return { status: 500, headers: {}, body: JSON.stringify({ __type: "com.amazonaws.dynamodb.v20120810#InternalServerError" }) };
      }
      return inner(call);
    };
    const h = harness({ transport, env: { EXPLAIN_DAILY_PERCENT: "1" } }); // $0.25/day
    const codes: string[] = [];
    for (let i = 0; i < 40; i++) {
      const r = await h.handler(evalEvent()) as EvaluationResult;
      codes.push(r.evaluation.code ?? "ok");
      if (r.evaluation.code === "E_HEADROOM" || r.evaluation.code === "E_PAUSE_FLAG") break;
    }
    const keys = spendKeys(h.clock.ms);
    const reserved = fa.items("billing#").filter(([k, i]) => k !== BILLING_PAUSE_KEY && (i.state as { S: string }).S === "reserved");
    console.log("M1 codes", codes.join(","), "| leaks", leaks, "modelCalls", fa.aws.modelCalls.length, "day m", fa.aws.table.num(keys.day, "m"), "/", 250_000,
      "| reserved events", reserved.length, "debts", fa.items("billingdebt#").length, "pause", fa.aws.table.items.has(BILLING_PAUSE_KEY));
    expect(fa.aws.modelCalls).toHaveLength(0);
    expect(codes.at(-1)).toBe("E_HEADROOM");
    expect(fa.items("billingdebt#")).toHaveLength(0);
  });

  it("M2 late commit: reserve lands after its readback -> E_DDB, then a permanent reserved event", async () => {
    const fa = new FaultAws();
    fa.fault = (op, b) => isReserveTx(op, b) ? "late-commit" : undefined;
    const h = harness({ transport: fa.transport });
    const r = await h.handler(evalEvent()) as EvaluationResult;
    await Promise.all(fa.lateCommits);
    const keys = spendKeys(h.clock.ms);
    console.log("M2", r.evaluation.code, "modelCalled", r.evaluation.modelCalled, "month m", fa.aws.table.num(keys.month, "m"), "reserved events",
      fa.items("billing#").filter(([k]) => k !== BILLING_PAUSE_KEY).length, "debts", fa.items("billingdebt#").length);
    expect(r.evaluation.code).toBe("E_DDB");
    expect(fa.aws.modelCalls).toHaveLength(0);
    expect(fa.aws.table.num(keys.month, "m")).toBeGreaterThan(0);
  });
});

describe("M3: settle lands after its readback", () => {
  it("records a debt and a pause for a settlement that in fact committed", async () => {
    const fa = new FaultAws();
    fa.fault = (op, b) => isSettleTx(op, b) ? "late-commit" : undefined;
    const h = harness({ transport: fa.transport });
    const r = await h.handler(evalEvent()) as EvaluationResult;
    await Promise.all(fa.lateCommits);
    const keys = spendKeys(h.clock.ms);
    const debt = fa.items("billingdebt#")[0]?.[1];
    const ev = fa.items("billing#").find(([k]) => k !== BILLING_PAUSE_KEY)?.[1];
    console.log("M3", r.evaluation.code, "pausePersisted", r.evaluation.pausePersisted, "| counters", fa.aws.table.num(keys.month, "m"), fa.aws.table.num(keys.day, "m"),
      "| event", JSON.stringify(ev?.state), JSON.stringify(ev?.actual), "| debt", JSON.stringify(debt && { reserved: debt.reserved, actual: debt.actual, reason: debt.reason }));
    expect(r.evaluation.code).toBe("E_SETTLE");
    expect((ev?.state as { S: string }).S).toBe("settled");
    expect(fa.aws.table.num(keys.month, "m")).toBe(r.evaluation.actualMicros);
    expect(debt).toBeDefined(); // debt says "unresolved" though counters already hold the actual
  });
});

describe("M4: double settlement", () => {
  it("concurrent duplicate settle / settle+release of one reservation apply once", async () => {
    const fa = new FaultAws();
    const ddb = new Ddb(fa.transport, cfg.region, cfg.table);
    const a = await reserve(ddb, cfg, now, 10_000);
    if (!a.ok) throw new Error("x");
    const res = await Promise.all([settle(ddb, a.reservation, 3000), settle(ddb, a.reservation, 3000), release(ddb, a.reservation), settle(ddb, a.reservation, 9000)]);
    const keys = spendKeys(now);
    console.log("M4", JSON.stringify(res), "month", fa.aws.table.num(keys.month, "m"), "day", fa.aws.table.num(keys.day, "m"));
    expect(res.filter(Boolean).length).toBe(2); // two identical settles report true, contradictory ones false
    expect(fa.aws.table.num(keys.month, "m")).toBe(3000);
    expect(fa.aws.table.num(keys.day, "m")).toBe(3000);
  });

  it("same, with real conflict semantics: the duplicate is cancelled, readback proves the first", async () => {
    const fa = new FaultAws(); fa.txMs = 10;
    const ddb = new Ddb(fa.transport, cfg.region, cfg.table);
    const a = await reserve(ddb, cfg, now, 10_000);
    if (!a.ok) throw new Error("x");
    const p1 = settle(ddb, a.reservation, 3000);
    await sleep(2);
    const p2 = settle(ddb, a.reservation, 3000); // conflicts; readback sees "reserved" (first not yet committed)
    const res = await Promise.all([p1, p2]);
    console.log("M4b", JSON.stringify(res), "month", fa.aws.table.num(spendKeys(now).month, "m"));
    expect(fa.aws.table.num(spendKeys(now).month, "m")).toBe(3000);
  });
});

describe("M5/M6: rollover and skew", () => {
  it("M5 durable pause written on Oct 31 23:59:59 still stops a fresh instance 13 months later; settle stays on Oct keys", async () => {
    const fa = new FaultAws();
    const h = harness({ transport: fa.transport });
    h.clock.ms = Date.UTC(2026, 9, 31, 23, 59, 59, 900);
    fa.aws.model = () => { h.clock.advance(500); return { status: 200, json: modelReply({ usage: null }) }; };
    const r = await h.handler(evalEvent()) as EvaluationResult;
    expect(r.evaluation.pausePersisted).toBe(true);
    console.log("M5 keys", [...fa.aws.table.items.keys()].filter((k) => k.startsWith("spend")).join(","));
    const fresh = harness({ transport: fa.transport });
    fresh.clock.ms = Date.UTC(2027, 10, 30);
    expect((await fresh.call(httpEvent())).statusCode).toBe(503);
    expect(lastLog(fresh).code).toBe("E_BILLING_PAUSE");
  });

  it("M6 an instance whose clock runs 5 s fast books into November while October is full", async () => {
    const fa = new FaultAws();
    const trueNow = Date.UTC(2026, 9, 31, 23, 59, 57);
    const oct = spendKeys(trueNow);
    fa.aws.table.items.set(oct.month, { pk: { S: oct.month }, m: { N: String(25_000_000) } });
    const slow = harness({ transport: fa.transport }); slow.clock.ms = trueNow;
    const fast = harness({ transport: fa.transport }); fast.clock.ms = trueNow + 5000;
    const rs = await slow.handler(evalEvent()) as EvaluationResult;
    const rf = await fast.handler(evalEvent()) as EvaluationResult;
    console.log("M6 slow", rs.evaluation.code ?? rs.status, "fast", rf.evaluation.code ?? rf.status, "keys", [...fa.aws.table.items.keys()].filter((k) => k.startsWith("spend")).join(","));
    expect(rf.status).toBe(200);
  });
});

describe("M7: pause readback errors", () => {
  it("settle committed with its bound pause, ack lost, pause readback fails -> app writes a second (E_SETTLE) debt for an already-settled event", async () => {
    const fa = new FaultAws();
    fa.aws.model = () => ({ status: 200, json: modelReply({ inTok: 50_000, outTok: 400 }) });
    let lose = false;
    const inner = fa.transport;
    const transport: typeof inner = async (call) => {
      if (call.service === "dynamodb" && call.body.includes(":settled")) { await inner(call); lose = true; throw new (await import("../../pr10b-wt/packages/explain/src/aws/transport.js")).TransportError("timeout"); }
      if (lose && call.service === "dynamodb" && call.body.includes('"billing#pause"') && call.body.includes("ConsistentRead")) {
        lose = false; return { status: 500, headers: {}, body: JSON.stringify({ __type: "x#InternalServerError" }) };
      }
      return inner(call);
    };
    const h = harness({ transport });
    const r = await h.handler(evalEvent()) as EvaluationResult;
    const keys = spendKeys(h.clock.ms);
    const debt = fa.items("billingdebt#")[0]?.[1];
    console.log("M7", r.evaluation.code, "counters", fa.aws.table.num(keys.month, "m"), "actual", r.evaluation.actualMicros, "debt", JSON.stringify(debt && { reason: debt.reason, actual: debt.actual }));
    expect(r.evaluation.code).toBe("E_SETTLE"); // the true cause (E_PROVIDER_BOUND) is replaced in log/eval
    expect(fa.aws.table.num(keys.month, "m")).toBe(r.evaluation.actualMicros);
  });

  it("reserve refused by a durable pause, readback GetItem fails -> E_DDB, instance not fenced", async () => {
    const fa = new FaultAws();
    fa.aws.table.items.set(BILLING_PAUSE_KEY, { pk: { S: BILLING_PAUSE_KEY }, reason: { S: "E_SETTLE" } });
    const h = harness({ transport: fa.transport });
    // Hide the pause from the cheap pre-read only, so the reserve transaction is what refuses.
    const pauseItem = fa.aws.table.items.get(BILLING_PAUSE_KEY)!;
    let first = true;
    fa.fault = (op, b) => {
      if (op === "GetItem" && JSON.stringify(b).includes("billing#pause") && first) { first = false; fa.aws.table.items.delete(BILLING_PAUSE_KEY); }
      if (isReserveTx(op, b)) fa.aws.table.items.set(BILLING_PAUSE_KEY, pauseItem);
      return undefined;
    };
    fa.aws.table.fault = (op, b) => op === "GetItem" && /"billing#[0-9a-f-]{36}"/.test(JSON.stringify(b)) ? "network" : undefined;
    const r = await h.handler(evalEvent()) as EvaluationResult;
    console.log("M7b", r.evaluation.code, "pausedUntil", h.deps.state.pausedUntil);
    expect(fa.aws.modelCalls).toHaveLength(0);
    expect(r.evaluation.code).toBe("E_DDB");
    expect(h.deps.state.pausedUntil).toBe(0);
  });
});
