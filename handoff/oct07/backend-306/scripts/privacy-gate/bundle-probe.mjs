// Import the exact built Lambda bytes with an otherwise-valid env for each
// reviewed model; record any network attempt.
const ids = { "us.xai.grok-4.7": ["2.2", "6.6"], "us.anthropic.claude-sonnet-5-5": ["2.2", "11"], "us.openai.gpt-6.1-sol": ["2.2", "11"] };
const id = process.argv[2];
const [pin, pout] = ids[id];
Object.assign(process.env, {
  AWS_REGION: "us-east-1", AWS_ACCESS_KEY_ID: "AKIDFAKE", AWS_SECRET_ACCESS_KEY: "secret", EXPLAIN_SWITCH: "on", EXPLAIN_TABLE: "biasclear-explain",
  EXPLAIN_MODEL_ID: id, EXPLAIN_PRICE_IN: pin, EXPLAIN_PRICE_OUT: pout, EXPLAIN_MONTHLY_CAP_USD: "25", EXPLAIN_DAILY_PERCENT: "10",
  EXPLAIN_ORIGINS: "https://biasclear.com", EXPLAIN_RETENTION_MODE: "none", EXPLAIN_RATE_10MIN: "10", EXPLAIN_RATE_DAY: "50", EXPLAIN_EVAL_KEY: "e".repeat(64),
});
const fetched = [];
globalThis.fetch = async (url) => { fetched.push(String(url)); return new Response("{}", { status: 200 }); };
const logs = [];
const orig = console.log; console.log = (...a) => logs.push(a.join(" "));
const { handler } = await import(new URL("../../pr10b-wt/packages/explain/dist/index.mjs", import.meta.url).href);
const r1 = await handler({ explainEvaluation: 1, key: "e".repeat(64), request: { v: 1 } });
const r2 = await handler({ version: "2.0", headers: { origin: "https://biasclear.com", "content-type": "application/json" }, body: "{}", requestContext: { http: { method: "POST", path: "/v1/explain", sourceIp: "203.0.113.9" } } });
console.log = orig;
console.log(JSON.stringify({ id, evalStatus: r1.status, evalCode: r1.evaluation?.code, httpStatus: r2.statusCode, fetched, logCodes: logs.map((l) => { try { return JSON.parse(l).code; } catch { return l.slice(0, 80); } }) }));
