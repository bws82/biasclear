import { describe, expect, it } from "vitest";
import { appendFileSync } from "node:fs";
import { TxDb } from "./txdb.js";
import { BILLING_PAUSE_KEY } from "../../pr10b-wt/packages/explain/src/spend.js";
import { harness, httpEvent, modelReply } from "../../pr10b-wt/packages/explain/test/helpers.js";

const out = (tag: string, o: unknown) => appendFileSync(import.meta.dirname + "/results.txt", `### ${tag} ${JSON.stringify(o)}\n`);
const SCALE = 100; // 1 real ms == 100 ms Lambda time

async function run(tag: string, o: { ddb: number; settings: number; model: number; timeout?: boolean; warm?: boolean; hangAfterModel?: boolean }) {
  const db = new TxDb();
  const h = harness({ transport: db.transport });
  // engine warm-up (compile patterns) outside the timed window
  db.aws.model = () => ({ status: 200, json: modelReply() });
  if (o.warm) { await h.call(httpEvent({ ip: "192.0.2.50" })); }
  else { const w = harness({ transport: db.transport }); await w.call(httpEvent({ ip: "192.0.2.51" })); db.aws.table.items.delete([...db.aws.table.items.keys()].find((k) => k.startsWith("salt#"))!); }
  db.starts = []; db.lat = { ddb: o.ddb / SCALE, settings: o.settings / SCALE, model: o.model / SCALE };
  let modelDone = 0;
  db.aws.model = () => { modelDone = performance.now() - db.t0; return o.timeout ? "timeout" : { status: 200, json: modelReply() }; };
  let sawModel = false;
  if (o.hangAfterModel) db.hook = (op) => (sawModel && op === "TransactWriteItems" ? "hang" : undefined);
  db.t0 = performance.now();
  const p = h.call(httpEvent({ ip: "192.0.2.9" }));
  if (o.hangAfterModel) {
    const orig = db.aws.model; db.aws.model = (b) => { sawModel = true; return orig(b); };
    const r = await Promise.race([p.then(() => "finished"), new Promise((res) => setTimeout(() => res("killed"), 2000))]);
    const logsAfter = h.logs.length;
    const ev = [...db.aws.table.items.entries()].filter(([k]) => k.startsWith("billing#") && k !== BILLING_PAUSE_KEY).map(([, it]) => ({ s: (it.state as { S: string }).S, ttlDays: Math.round((Number((it.ttl as { N: string }).N) - h.clock.ms / 1000) / 86400) }));
    const fresh = harness({ transport: db.transport }); db.lat = { ddb: 0, settings: 0, model: 0 }; db.hook = undefined;
    db.aws.model = () => ({ status: 200, json: modelReply() });
    const rc = await fresh.call(httpEvent({ ip: "192.0.2.77" }));
    out(tag, { r, logLinesFromKilledReq: logsAfter - (o.warm ? 1 : 0), events: ev, pause: db.item(BILLING_PAUSE_KEY) !== undefined, debts: db.keys("billingdebt#").length, freshStatus: rc.statusCode, modelCalls: db.aws.modelCalls.length });
    return;
  }
  await p;
  const s = db.starts.map((x) => `${(x.t * SCALE / 1000).toFixed(2)}s ${x.what.replace(/billing#[0-9a-f-]{36}/g, "billing#<ev>").replace(/[0-9a-f]{32}/g, "<h>")}`);
  const post = db.starts.filter((x) => x.t > modelDone && x.what.startsWith("TransactWriteItems"));
  out(tag, { code: JSON.parse(h.logs.at(-1)!).code, modelEnd_s: +(modelDone * SCALE / 1000).toFixed(2), firstPostModelTx_s: post[0] ? +(post[0].t * SCALE / 1000).toFixed(2) : null, calls: s });
}

describe("F3 deadline", () => {
  it("cold instance, ddb 1s, settings 1s, model 19.5s valid", () => run("F3-cold-1s-19.5", { ddb: 1000, settings: 1000, model: 19500 }));
  it("cold instance, ddb 1s, model times out at 20s", () => run("F3-cold-1s-timeout", { ddb: 1000, settings: 1000, model: 20000, timeout: true }));
  it("warm instance, ddb 1s, model 20s timeout", () => run("F3-warm-1s-timeout", { ddb: 1000, settings: 1000, model: 20000, timeout: true, warm: true }));
  it("cold instance, ddb 20ms, settings 200ms, model 19.9s", () => run("F3-cold-normal", { ddb: 20, settings: 200, model: 19900 }));
  it("kill stand-in: tx after model hangs", () => run("F3-kill", { ddb: 0, settings: 0, model: 0, timeout: true, warm: true, hangAfterModel: true }));
});
