import { harness, httpEvent, modelReply, ENV, lastLog, evalEvent, EVAL_KEY } from "/tmp/claude-0/-home-user-biasclear/bb187462-b843-5453-a36d-b91a5ff093cc/scratchpad/pr10-wt/packages/explain/test/helpers.ts";
import { readConfig } from "/tmp/claude-0/-home-user-biasclear/bb187462-b843-5453-a36d-b91a5ff093cc/scratchpad/pr10-wt/packages/explain/src/config.ts";
import { MODELS } from "/tmp/claude-0/-home-user-biasclear/bb187462-b843-5453-a36d-b91a5ff093cc/scratchpad/pr10-wt/packages/explain/src/models.ts";

const SON = { ...ENV, EXPLAIN_MODEL_ID: "us.anthropic.claude-sonnet-5-5", EXPLAIN_PRICE_OUT: "11.00" };
const MONTH = "spend#2026-10", DAY = "spendday#2026-10-05";

async function overrun() {
  const cfg = readConfig(SON)!;
  const h = harness({ config: cfg });
  h.aws.model = () => ({ status: 200, json: modelReply({ outTok: 2_000_000 }) });
  const r = await h.call(httpEvent());
  console.log("A overrun (Sonnet, real readConfig, outputTokens=2,000,000 > maxTokens 400): status", r.statusCode,
    "log", JSON.stringify(lastLog(h)), "month m", h.aws.table.num(MONTH, "m"), "cap", cfg.capMicros, "day cap", cfg.dailyMicros);
  const r2 = await h.call(httpEvent({ ip: "203.0.113.9" }));
  console.log("   next request:", r2.statusCode, lastLog(h).code, "pausedUntil", h.deps.state.pausedUntil);
}

async function grokFallback() {
  const h = harness(); // stub config, Grok, billedMaxTokens null
  h.aws.model = () => ({ status: 200, json: modelReply({ outTok: 30_000 }) });
  const r = await h.call(httpEvent());
  const l = lastLog(h);
  console.log("B Grok via non-readConfig Config: status", r.statusCode, "reserved basis maxTokens=", MODELS["us.xai.grok-4.7"]!.maxTokens, "log", JSON.stringify(l));
}

async function concurrency() {
  const cfg = readConfig(SON)!;
  const h = harness({ config: cfg });
  h.aws.table.delayMs = 1;
  // every call maybe-billed (timeout) so reservations never come back
  h.aws.model = () => "timeout";
  const N = 400;
  const rs = await Promise.all(Array.from({ length: N }, (_, i) => h.call(httpEvent({ ip: `198.51.${i >> 8}.${i & 255}` }))));
  const counts: Record<string, number> = {};
  for (const r of rs) counts[r.statusCode] = (counts[r.statusCode] ?? 0) + 1;
  console.log("C concurrency (", N, "parallel, all maybe-billed): statuses", JSON.stringify(counts), "model calls", h.aws.modelCalls.length,
    "day m", h.aws.table.num(DAY, "m"), "<= dailyMicros", cfg.dailyMicros, "month m", h.aws.table.num(MONTH, "m"));
}

async function settleFailOnOverrun() {
  const cfg = readConfig(SON)!;
  const h = harness({ config: cfg });
  h.aws.model = () => ({ status: 200, json: modelReply({ outTok: 100_000 }) });
  let reserves = 0;
  h.aws.table.fault = (op, p) => (op === "UpdateItem" && (p.UpdateExpression as string).startsWith("ADD #m") ? "network" : undefined);
  const r = await h.call(httpEvent());
  const l = lastLog(h);
  console.log("D settle fails on an overrun: status", r.statusCode, "logged micros", l.micros, "code", l.code, "month m", h.aws.table.num(MONTH, "m"),
    "true cost micros", Math.ceil((820 * 2200 + 100_000 * 11000) / 1000));
}

async function evalBypass() {
  const cfg = readConfig(SON)!;
  const h = harness({ config: { ...cfg, evalKey: EVAL_KEY } });
  const r = await h.handler(evalEvent());
  console.log("E eval invoke reserves too:", JSON.stringify((r as any).evaluation), "month m", h.aws.table.num(MONTH, "m"));
}

async function worst() {
  const cfg = readConfig(SON)!;
  const h = harness({ config: cfg });
  h.aws.model = () => "timeout";
  await h.call(httpEvent());
  console.log("F worst-case reservation micros (Sonnet, sample sentence):", h.aws.table.num(MONTH, "m"));
}

await overrun(); await grokFallback(); await concurrency(); await settleFailOnOverrun(); await evalBypass(); await worst();
