// Red-team lens iam-logs-docs. Executes the real handler (stub model registry
// from the package's own test helpers) through the REAL fetchTransport + SigV4
// signer, with a fetchImpl that routes to the package's in-memory FakeAws.
// Checks: (1) no canary/visitor text, error text or stack reaches any output
// stream on paths the package's nolog suite does not cover (bound breach,
// E_SETTLE with failed durable pause, unknown usage, SigV4/fetch errors);
// (2) per-region SigV4 scopes; (3) the billing-anomaly metric filter against
// the app line as written AND as Lambda's JSON log format would wrap it;
// (4) which AWS operations the function actually performs (for IAM diffing).
import { afterAll, afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { readFileSync, writeFileSync } from "node:fs";
import {
  FakeAws, harness, httpEvent, modelReply, requestBody, evalEvent, type Harness,
} from "../../pr10b-wt/packages/explain/test/helpers.js";
import { fetchTransport } from "../../pr10b-wt/packages/explain/src/aws/transport.js";

const ROOT = new URL("../../pr10b-wt/", import.meta.url).pathname;
const CANARY = "Zq9RedTeamCanary";
const CANARY_SENTENCE = `Every serious economist agrees that the ${CANARY} plan will lower rents within two years.`;
const OUT = new URL("./", import.meta.url).pathname;

let captured: string[] = [];
const rejections: unknown[] = [];
const warnings: unknown[] = [];
const onRej = (r: unknown) => rejections.push(r);
const onWarn = (w: unknown) => warnings.push(w);
process.on("unhandledRejection", onRej);
process.on("warning", onWarn);

beforeEach(() => {
  captured = [];
  const grab = (...args: unknown[]) => { captured.push(args.map((a) => (typeof a === "string" ? a : String(a))).join(" ")); };
  for (const m of ["log", "info", "warn", "error", "debug", "trace"] as const) vi.spyOn(console, m).mockImplementation(grab);
  vi.spyOn(process.stdout, "write").mockImplementation((c: unknown) => { captured.push(String(c)); return true; });
  vi.spyOn(process.stderr, "write").mockImplementation((c: unknown) => { captured.push(String(c)); return true; });
});
afterEach(() => { vi.restoreAllMocks(); });

const ALLOWED = new Set(["outcome", "status", "ms", "code", "rule", "rules", "model", "inTok", "outTok", "micros", "overrun",
  "plainer", "evaluation", "reservedMicros", "actualMicros", "pausePersisted", "billedBoundViolated"]);
function expectClean(h: Harness): void {
  const all = [...h.logs, ...captured].join("\n");
  expect(all).not.toContain(CANARY);
  expect(all).not.toMatch(/\bat .+:\d+:\d+/);
  expect(all).not.toMatch(/SyntaxError|RangeError|TypeError|Unexpected token|is not valid JSON|AWS4-HMAC|Credential=/);
  for (const line of h.logs) for (const k of Object.keys(JSON.parse(line))) expect(ALLOWED.has(k), k).toBe(true);
}

/** Real transport + signer; fetch is routed to the package's FakeAws. */
interface Sent { host: string; path: string; region: string; service: string; target: string }
function realTransportHarness(mutate?: (aws: FakeAws, url: URL, init: RequestInit) => Response | undefined) {
  const sent: Sent[] = [];
  let aws!: FakeAws;
  const fetchImpl = (async (input: string, init: RequestInit) => {
    const url = new URL(input);
    const headers = init.headers as Record<string, string>;
    const scope = /Credential=[^/]+\/\d{8}\/([^/]+)\/([^/]+)\/aws4_request/.exec(headers.authorization ?? "");
    sent.push({ host: url.host, path: url.pathname, region: scope?.[1] ?? "?", service: scope?.[2] ?? "?", target: headers["x-amz-target"] ?? "" });
    const m = mutate?.(aws, url, init);
    if (m) return m;
    const service = url.host.startsWith("dynamodb.") ? "dynamodb" : "bedrock";
    const r = await aws.transport({ service, host: url.host, method: init.method as "GET" | "POST", path: url.pathname,
      headers, body: (init.body as string) ?? "", timeoutMs: 1000 });
    return new Response(r.body, { status: r.status, headers: r.headers });
  }) as unknown as typeof fetch;
  const h = harness();
  aws = h.aws;
  const transport = fetchTransport({ region: "us-east-1", env: { AWS_ACCESS_KEY_ID: "AKIDEXAMPLE", AWS_SECRET_ACCESS_KEY: "secret", AWS_SESSION_TOKEN: "tok" }, now: h.clock.now, fetchImpl });
  const h2 = harness({ transport });
  // share the FakeAws of h2 so table/model scripting applies
  aws = h2.aws;
  return { h: h2, sent };
}

const lines: Record<string, string> = {};

describe("logs stay fixed-shape and text-free on paths nolog.test.ts does not cover", () => {
  it("billed bound breach (outTok > billedMaxTokens) through real SigV4 transport", async () => {
    const { h, sent } = realTransportHarness();
    h.aws.model = () => ({ status: 200, json: modelReply({ how: `The words "Every serious economist agrees" about ${CANARY}.`, outTok: 999 }) });
    const r = await h.call(httpEvent({ body: requestBody({ sentence: CANARY_SENTENCE }), headers: { "user-agent": CANARY } }));
    expect(r.statusCode).toBe(503);
    const log = JSON.parse(h.logs.at(-1)!);
    expect(log).toMatchObject({ code: "E_PROVIDER_BOUND", billedBoundViolated: 1, pausePersisted: 1 });
    lines.bound = h.logs.at(-1)!;
    expectClean(h);
    // per-region SigV4: every /data-retention read is signed for its own region
    const ret = sent.filter((s) => s.path === "/data-retention");
    expect(ret.map((s) => `${s.host}|${s.region}|${s.service}`).sort()).toEqual([
      "bedrock.us-east-1.amazonaws.com|us-east-1|bedrock", "bedrock.us-east-2.amazonaws.com|us-east-2|bedrock", "bedrock.us-west-2.amazonaws.com|us-west-2|bedrock"]);
    const logging = sent.filter((s) => s.path === "/logging/modelinvocations");
    expect(logging.map((s) => s.region)).toEqual(["us-east-1"]);
    writeFileSync(`${OUT}ops-observed.json`, JSON.stringify(sent, null, 1));
  });

  it("E_SETTLE where the durable pause write ALSO fails -> pausePersisted 0", async () => {
    const h = harness();
    let tx = 0;
    h.aws.table.fault = (op) => (op === "TransactWriteItems" && ++tx > 1 ? "throttle" : undefined);
    h.aws.model = () => ({ status: 200, json: modelReply({ how: `about ${CANARY}` }) });
    const r = await h.call(httpEvent({ body: requestBody({ sentence: CANARY_SENTENCE }) }));
    expect(r.statusCode).toBe(503);
    expect(JSON.parse(h.logs.at(-1)!)).toMatchObject({ code: "E_SETTLE", pausePersisted: 0 });
    lines.settleUnpersisted = h.logs.at(-1)!;
    expectClean(h);
  });

  it("unknown usage (no usage block) -> pause, no actualMicros invented", async () => {
    const h = harness();
    h.aws.model = () => ({ status: 200, json: modelReply({ usage: null, how: CANARY }) });
    const r = await h.call(httpEvent({ body: requestBody({ sentence: CANARY_SENTENCE }) }));
    expect(r.statusCode).toBe(503);
    const log = JSON.parse(h.logs.at(-1)!);
    expect(log.code).toBe("E_MODEL_NO_USAGE");
    expect(log.actualMicros).toBeUndefined();
    expect(log.pausePersisted).toBe(1);
    lines.noUsage = h.logs.at(-1)!;
    expectClean(h);
  });

  it("fetch rejects with the signed request and canary in message/cause (real SigV4 transport)", async () => {
    const { h } = realTransportHarness((_aws, _url, init) => {
      throw new TypeError(`fetch failed ${CANARY} ${String((init.headers as Record<string, string>).authorization)}`, { cause: new Error(CANARY) });
    });
    const r = await h.call(httpEvent({ body: requestBody({ sentence: CANARY_SENTENCE }) }));
    expect(r.statusCode).toBe(503);
    expect(JSON.parse(h.logs.at(-1)!).code).toBe("E_SETTINGS_READ");
    expectClean(h);
  });

  it("Bedrock 400 with canary in x-amzn-errortype and body, via real transport", async () => {
    const { h } = realTransportHarness((_aws, url) => url.host.startsWith("bedrock-runtime.")
      ? new Response(JSON.stringify({ message: `retention ${CANARY}` }), { status: 400, headers: { "x-amzn-errortype": `ValidationException:${CANARY}` } })
      : undefined);
    const r = await h.call(httpEvent({ body: requestBody({ sentence: CANARY_SENTENCE }) }));
    expect(r.statusCode).toBe(503);
    expect(JSON.parse(h.logs.at(-1)!).code).toBe("E_MODEL_RETENTION");
    expectClean(h);
  });

  it("DynamoDB error body quoting the request, via real transport", async () => {
    const { h } = realTransportHarness((_aws, url, init) => url.host.startsWith("dynamodb.") && String(init.body).includes("TransactItems")
      ? new Response(JSON.stringify({ __type: `x#${CANARY}`, message: String(init.body) }), { status: 400 }) : undefined);
    const r = await h.call(httpEvent({ body: requestBody({ sentence: CANARY_SENTENCE }) }));
    expect(r.statusCode).toBe(503);
    expect(JSON.parse(h.logs.at(-1)!).code).toBe("E_DDB");
    expectClean(h);
  });

  it("evaluation event with a wrong key logs no key", async () => {
    const h = harness();
    await h.handler(evalEvent(requestBody({ sentence: CANARY_SENTENCE }), "f".repeat(64)));
    const log = h.logs.join("\n");
    expect(log).not.toContain("f".repeat(64));
    expectClean(h);
  });
});

// ---- the billing-anomaly metric filter ----------------------------------
// Minimal evaluator for the exact OR-of-equalities JSON pattern in explain.yaml.
function filterPattern(): string {
  const yaml = readFileSync(`${ROOT}infra/aws/explain.yaml`, "utf8");
  return /FilterPattern: '(.+)'/.exec(yaml)![1]!;
}
function matches(pattern: string, event: string): boolean {
  let obj: unknown;
  try { obj = JSON.parse(event); } catch { return false; } // JSON filters never match non-JSON events
  if (obj === null || typeof obj !== "object") return false;
  const conds = [...pattern.matchAll(/\(\$\.([A-Za-z]+) = ("[^"]*"|-?\d+)\)/g)];
  expect(conds.length).toBe(5);
  return conds.some(([, field, raw]) => {
    const want: unknown = raw!.startsWith('"') ? raw!.slice(1, -1) : Number(raw);
    return (obj as Record<string, unknown>)[field!] === want; // `$.x` selects a top-level field only
  });
}
/** Lambda managed Node.js runtime, LoggingConfig.LogFormat=JSON, console.log(oneString):
 * documented envelope {timestamp, level, requestId, message} with the string as `message`. */
function lambdaJsonEnvelope(line: string): string {
  return JSON.stringify({ timestamp: "2026-10-07T00:00:00.000Z", level: "INFO", requestId: "00000000-0000-0000-0000-000000000000", message: line });
}
function lambdaTextLine(line: string): string {
  return `2026-10-07T00:00:00.000Z\t00000000-0000-0000-0000-000000000000\tINFO\t${line}`;
}

describe("billing-anomaly metric filter vs. what Lambda actually stores", () => {
  it("matches the bare app line but NOT the line as Lambda's JSON (or Text) log format stores it", () => {
    const p = filterPattern();
    const report: Record<string, unknown> = { pattern: p };
    for (const [name, line] of Object.entries(lines)) {
      const env = lambdaJsonEnvelope(line);
      report[name] = { appLine: line, bareMatches: matches(p, line), lambdaJsonMatches: matches(p, env),
        envelopeMessageType: typeof (JSON.parse(env) as { message: unknown }).message, lambdaTextMatches: matches(p, lambdaTextLine(line)) };
      expect(matches(p, line)).toBe(true);
      expect(matches(p, env)).toBe(false);
      expect(matches(p, lambdaTextLine(line))).toBe(false);
    }
    writeFileSync(`${OUT}metric-filter-result.json`, JSON.stringify(report, null, 1));
  });
});

afterAll(() => {
  process.off("unhandledRejection", onRej);
  process.off("warning", onWarn);
  writeFileSync(`${OUT}process-events.json`, JSON.stringify({ unhandledRejections: rejections.map(String), warnings: warnings.map(String) }));
  expect(rejections).toEqual([]);
});
