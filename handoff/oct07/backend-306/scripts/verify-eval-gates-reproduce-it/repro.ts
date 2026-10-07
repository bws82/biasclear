// Independent reproduction of eval-gate findings against the checked-out source (read-only).
// Rows are produced by the REAL handler (createHandler) with the in-memory test doubles,
// shaped exactly as infra/aws/ops.sh evaluate writes them: {id, part, sample, status, body, evaluation}.
import { readFileSync } from "node:fs";
import { evaluationRequests, report, classifySample, refusalLike, sampleOf, type Fixtures, type HumanReview, type RawLine, type PlannedCall } from "../../pr10b-wt/packages/explain/ops/ops.ts";
import { harness, modelReply, EVAL_KEY, STUB_MODELS, ENV } from "../../pr10b-wt/packages/explain/test/helpers.ts";

const FIX = process.argv[2]!;
const corpus = JSON.parse(readFileSync(FIX, "utf8")) as Fixtures;
const MODEL_ID = ENV.EXPLAIN_MODEL_ID!;
const DISPLAY = STUB_MODELS[MODEL_ID]!.displayName;

type Reply = { status: number; json?: unknown } | "network";
interface Plan {
  transform?: (c: PlannedCall) => Record<string, unknown>;       // what the (drifted) deployment receives/accepts
  reply?: (c: PlannedCall) => Reply;                              // the scripted provider
  settleFault?: (c: PlannedCall) => boolean;                      // make settlement fail for this call
}
const okHow = (c: PlannedCall) => {
  const s = c.request.sentence as string; const mark = s.slice(c.request.start as number, c.request.end as number);
  return `The words "${mark}" frame the claim for the reader. The sentence gives no further reason for that framing.`;
};
const defaultReply = (f: Fixtures) => (c: PlannedCall): Reply => {
  const rw = f.rewrites?.find((r) => r.id === c.id && c.part === "r");
  return { status: 200, json: modelReply({ how: okHow(c), plainer: rw ? rw.safeRewrite : (c.request.sentence as string), inTok: 100, outTok: 40 }) };
};

async function live(f: Fixtures, plan: Plan = {}): Promise<{ planned: PlannedCall[]; raw: RawLine[] }> {
  const planned = evaluationRequests(f);
  const h = harness();
  const raw: RawLine[] = [];
  for (const c of planned) {
    const rep = (plan.reply ?? defaultReply(f))(c);
    h.aws.model = () => rep;
    const failSettle = plan.settleFault?.(c) ?? false;
    let reserved = false;
    h.aws.table.fault = failSettle ? (op, payload) => {
      // The first TransactWriteItems is the reservation; the second is settlement.
      if (op === "TransactWriteItems") { if (!reserved) { reserved = true; return undefined; } return "throttle"; }
      return undefined;
    } : undefined;
    const result = await h.handler({ explainEvaluation: 1, key: EVAL_KEY, request: plan.transform ? plan.transform(c) : c.request }) as Record<string, unknown>;
    h.aws.table.fault = undefined;
    h.clock.advance(1);
    // ops.sh: jq '{id: $meta.id, part: $meta.part, sample: $meta.sample, status, body, evaluation}'
    const line = JSON.parse(JSON.stringify({ id: c.id, part: c.part, sample: c.sample, status: result.status, body: result.body, evaluation: result.evaluation }));
    raw.push(line);
    const body = result.body as { error?: string };
    if (result.status === 503 && body?.error === "paused") break; // ops.sh stops here
  }
  return { planned, raw };
}

/** The most favourable possible independent review, bound to these exact bytes. */
function fullReview(f: Fixtures, raw: RawLine[], modelId: string | null): HumanReview {
  const pending = report(f, evaluationRequests(f).length, raw, { model: DISPLAY, modelId: MODEL_ID });
  const answers: HumanReview["answers"] = {};
  for (const p of evaluationRequests(f)) answers[`${p.id}/${p.part}/${p.sample}`] = { injection: "safe", rewrite: "preserved", useful: true };
  const r: Record<string, unknown> = { fixtureHash: pending.results.fixtureHash, rawHash: pending.results.rawHash, reviewer: "Independent reviewer", answers };
  if (modelId !== null) r.model = modelId;
  return r as unknown as HumanReview;
}
function score(f: Fixtures, planned: PlannedCall[], raw: RawLine[], opts: { model?: string; modelId?: string } = { model: DISPLAY, modelId: MODEL_ID }) {
  const review = fullReview(f, raw, opts.modelId ?? null);
  return report(f, planned.length, raw, { ...opts, review, plannedRequests: planned });
}
function show(name: string, r: ReturnType<typeof report>, keys: string[]) {
  const g = r.results.gates as Record<string, boolean>;
  console.log(`\n=== ${name}`);
  console.log(`ok=${r.ok} allGatesPass=${r.results.allGatesPass} complete=${r.results.complete} failing=${JSON.stringify(Object.entries(g).filter(([, v]) => !v).map(([k]) => k))}`);
  console.log(JSON.stringify(Object.fromEntries(keys.map((k) => [k, r.results[k]]))));
}
const outcomesBy = (r: ReturnType<typeof report>, part: string) => {
  const m: Record<string, number> = {};
  for (const x of r.results.perAnswer as Array<{ part: string; outcome: string }>) if (x.part === part) m[x.outcome] = (m[x.outcome] ?? 0) + 1;
  return m;
};

const which = process.argv[3] ?? "all";

// ---------- Baseline: real handler, no drift
if (which === "all" || which === "f1") {
  const { planned, raw } = await live(corpus);
  const r = score(corpus, planned, raw);
  show("F1-baseline real handler, current build, all clean answers", r, ["planned", "ran", "preflightRejected", "answered", "unknown"]);
  for (const p of ["a", "b", "i", "r", "c"]) console.log(` part ${p}:`, JSON.stringify(outcomesBy(r, p)));

  // F1: deployed build drifts so that every injection and rewrite request is rejected at preflight.
  // Simulated by sending a span that is not a mark (real handler returns 422 E_NOT_A_MARK, modelCalled:false).
  const drift = await live(corpus, { transform: (c) => (c.part === "i" || c.part === "r") ? { ...c.request, end: (c.request.end as number) - 1 } : c.request });
  const r1 = score(corpus, drift.planned, drift.raw);
  show("F1-drift injections+rewrites all preflight-rejected", r1, ["planned", "ran", "preflightRejected", "answered", "unknownn", "unreviewedAcceptedInjections", "unreviewedKeptRewrites", "changedProtectedRewrites"]);
  for (const p of ["i", "r"]) console.log(` part ${p}:`, JSON.stringify(outcomesBy(r1, p)));
  const sample = drift.raw.find((l) => l.part === "i")!;
  console.log(" example drifted injection row:", JSON.stringify({ status: sample.status, body: sample.body, evaluation: sample.evaluation }));
  console.log(" gates.injection=", (r1.results.gates as Record<string, boolean>).injection, " gates.claimMeaning=", (r1.results.gates as Record<string, boolean>).claimMeaning);

  // F1 sub-claim: whole pair preflight-rejected on both sides (deterministic per request) -> parity?
  const pairDrift = await live(corpus, { transform: (c) => (c.id === "p01") ? { ...c.request, end: (c.request.end as number) - 1 } : c.request });
  const r1b = score(corpus, pairDrift.planned, pairDrift.raw);
  show("F1-pair p01 preflight-rejected on both sides for all samples (deterministic)", r1b, ["preflightRejected", "zeroEligiblePairs"]);
  // Are identical requests per sample? (deterministic preflight => partial-sample preflight impossible)
  const p01 = planned.filter((c) => c.id === "p01" && c.part === "a").map((c) => JSON.stringify(c.request));
  console.log(" p01/a requests identical across samples:", new Set(p01).size === 1);
}

if (which === "all" || which === "f2") {
  // F2: refusal wording. p01 sample 0: side a gets a refusal, side b gets a non-refusal reply the checker rejects.
  const f = corpus;
  const variants: Array<[string, string]> = [
    ["ascii", "I'm sorry, but I can't help with content about this group."],
    ["curly", "I’m sorry, but I can’t help with content about this group."],
    ["not-able", "I'm not able to help with content about this group."],
    ["unfortunately", "Unfortunately, I can't help with that."],
    ["decline", "I must decline to analyze this sentence."],
    ["will-not", "I will not answer this."],
    ["json-curly", JSON.stringify({ how: "I’m sorry, but I can’t help with that." })],
  ];
  for (const [name, text] of variants) {
    const { planned, raw } = await live(f, { reply: (c) => {
      if (c.id === "p01" && c.sample === 0 && c.part === "a") return { status: 200, json: modelReply({ text, inTok: 100, outTok: 40 }) };
      if (c.id === "p01" && c.sample === 0 && c.part === "b") return { status: 200, json: modelReply({ text: "Here is the analysis you asked for, in prose.", inTok: 100, outTok: 40 }) };
      return defaultReply(f)(c);
    } });
    const r = score(f, planned, raw);
    const pa = raw.find((l) => l.id === "p01" && l.part === "a" && l.sample === 0)!, pb = raw.find((l) => l.id === "p01" && l.part === "b" && l.sample === 0)!;
    const sa = sampleOf(pa), sb = sampleOf(pb);
    console.log(`\n=== F2 ${name}: a=${sa.status}/${sa.code} class=${classifySample(sa)} refusalLike=${refusalLike(sa)} | b=${sb.status}/${sb.code} class=${classifySample(sb)}`);
    console.log(`ok=${r.ok} allGatesPass=${r.results.allGatesPass} refusalParity=${(r.results.gates as Record<string, boolean>).refusalParity} answerParity=${(r.results.gates as Record<string, boolean>).answerParity} unmatchedRefusalOutcomes=${r.results.unmatchedRefusalOutcomes}`);
  }
}

if (which === "all" || which === "f4") {
  const { planned, raw } = await live(corpus);
  const r = score(corpus, planned, raw, {});
  show("F4 report() with no model/modelId and a review with no model key", r, ["model", "modelId", "reviewBound", "wrongModelLabels"]);
}

if (which === "all" || which === "f6") {
  // F6: last planned call gets a refusal-like reply with usage, then settlement fails -> 503 paused E_SETTLE.
  const lastKey = (() => { const p = evaluationRequests(corpus).at(-1)!; return `${p.id}/${p.part}/${p.sample}`; })();
  for (const text of ["Sorry, I can't help with that.", JSON.stringify({ how: "The sentence frames a choice." })]) {
    const { planned, raw } = await live(corpus, {
      reply: (c) => `${c.id}/${c.part}/${c.sample}` === lastKey ? { status: 200, json: modelReply({ text, inTok: 100, outTok: 40 }) } : defaultReply(corpus)(c),
      settleFault: (c) => `${c.id}/${c.part}/${c.sample}` === lastKey,
    });
    const last = raw.at(-1)!;
    const s = sampleOf(last);
    const r = score(corpus, planned, raw);
    console.log(`\n=== F6 last=${lastKey} text=${JSON.stringify(text).slice(0, 40)} row status=${last.status} body=${JSON.stringify(last.body)} code=${s.code} modelCalled=${s.modelCalled} inTok=${s.inTok} pausePersisted=${s.pausePersisted} class=${classifySample(s)}`);
    console.log(`ran=${r.results.ran}/${r.results.planned} ok=${r.ok} allGatesPass=${r.results.allGatesPass} complete=${r.results.complete} serviceBlocked=${r.results.serviceBlocked} unknown=${r.results.unknown} failing=${JSON.stringify(Object.entries(r.results.gates as Record<string, boolean>).filter(([, v]) => !v).map(([k]) => k))}`);
    console.log((r.markdown.split("\n").find((l) => l.startsWith("All ") || l.startsWith("**Incomplete")) ?? "").slice(0, 120));
  }
}

if (which === "dump") {
  // Writes raw.jsonl exactly as ops.sh would, plus a full review WITHOUT a model key and one WITH it.
  const { writeFileSync } = await import("node:fs");
  const { raw } = await live(corpus);
  writeFileSync("raw.jsonl", raw.map((l) => JSON.stringify(l)).join("\n") + "\n");
  // The CLI hashes the raw lines it parses from the file; recompute via report() on the parsed lines.
  const parsed = readFileSync("raw.jsonl", "utf8").split("\n").filter((l) => l.trim()).map((l) => JSON.parse(l));
  writeFileSync("review-nomodel.json", JSON.stringify(fullReview(corpus, parsed, null)));
  writeFileSync("review-model.json", JSON.stringify(fullReview(corpus, parsed, MODEL_ID)));
  console.log("dumped", raw.length, "rows; model id", MODEL_ID, "display", DISPLAY);
}
