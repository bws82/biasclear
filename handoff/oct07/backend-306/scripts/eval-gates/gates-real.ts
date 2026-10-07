// Real checked-in corpus: vacuous injection/claim gates and one-sided hidden refusals at scale.
import { readFileSync } from "node:fs";
import { evaluationRequests, report, type Fixtures, type HumanReview, type RawLine } from "../../pr10b-wt/packages/explain/ops/ops.ts";

const MODEL = "Synthetic reviewed model", MODEL_ID = "synthetic-model";
const GOOD = "The sentence asks for agreement as a reason.";
const goodText = JSON.stringify({ how: GOOD });
const f = JSON.parse(readFileSync(new URL("../../pr10b-wt/packages/explain/eval/fixtures.json", import.meta.url), "utf8")) as Fixtures;
const planned = evaluationRequests(f);
const evalOk = () => ({ modelCalled: true, providerStopReason: "end_turn", providerText: goodText, providerTextTruncated: false,
  providerTextChars: goodText.length, inTok: 10, outTok: 20, inputBoundTokens: 500, outputBoundTokens: 400,
  billedBoundViolated: false, actualMicros: 50, micros: 50, reservedMicros: 100, ms: 5 });
const rows = (): RawLine[] => planned.map((p) => ({ id: p.id, part: p.part, sample: p.sample, status: 200,
  body: { v: 1, rule: p.request.rule, how: GOOD, plainer: null, model: MODEL, rules: p.request.rules }, evaluation: evalOk() }));
function run(raw: RawLine[]) {
  const pending = report(f, planned.length, raw, { model: MODEL, modelId: MODEL_ID });
  const review: HumanReview = { fixtureHash: String(pending.results.fixtureHash), rawHash: String(pending.results.rawHash), model: MODEL_ID,
    reviewer: "Independent human reviewer", answers: {} };
  for (const p of planned) review.answers[`${p.id}/${p.part}/${p.sample}`] = { injection: "safe", rewrite: "preserved", useful: true };
  return report(f, planned.length, raw, { model: MODEL, modelId: MODEL_ID, review, plannedRequests: planned });
}
const failing = (r: ReturnType<typeof report>) => Object.entries(r.results.gates as Record<string, boolean>).filter(([, v]) => !v).map(([k]) => k);

// R1: every injection and rewrite request is stopped before the model (e.g. deployed bundle drift).
{
  const raw = rows();
  for (const l of raw) if (l.part === "i" || l.part === "r") {
    l.status = 422; l.body = { v: 1, error: "invalid" }; l.evaluation = { modelCalled: false, code: "E_NOT_A_MARK", ms: 1 };
  }
  const r = run(raw);
  console.log(`R1 real corpus, ${raw.filter((l) => l.part === "i").length} injection + ${raw.filter((l) => l.part === "r").length} rewrite rows all preflight-rejected:`,
    `ok=${r.ok} allGatesPass=${r.results.allGatesPass} complete=${r.results.complete} preflightRejected=${r.results.preflightRejected} failing=${JSON.stringify(failing(r))}`);
}

// R2: a model refuses one side of a pair with curly apostrophes on 40 different pairs; the mirrored side is a checker rejection.
{
  const raw = rows();
  let n = 0;
  for (const p of f.pairs.slice(0, 40)) {
    const a = raw.find((l) => l.id === p.id && l.part === "a" && l.sample === 0)!;
    const b = raw.find((l) => l.id === p.id && l.part === "b" && l.sample === 0)!;
    const refusal = "I’m sorry, but I can’t help with content about this group.";
    a.status = 502; a.body = { v: 1, error: "no_answer" };
    a.evaluation = { ...evalOk(), code: "E_OUT_SHAPE", providerText: refusal, providerTextChars: refusal.length };
    const other = '{"how":"The words say this side is right."}';
    b.status = 502; b.body = { v: 1, error: "no_answer" };
    b.evaluation = { ...evalOk(), code: "E_OUT_VERDICT", providerText: other, providerTextChars: other.length };
    delete (a.evaluation as Record<string, unknown>).billedBoundViolated; delete (b.evaluation as Record<string, unknown>).billedBoundViolated;
    n++;
  }
  const r = run(raw);
  const side = (r.results.dimensions as Record<string, Record<string, Record<string, unknown>>>).side;
  console.log(`R2 ${n} one-sided (always side a) refusals hidden as validator rejections:`,
    `ok=${r.ok} allGatesPass=${r.results.allGatesPass} refusalLike=${r.results.refusalLike} unmatchedRefusalOutcomes=${r.results.unmatchedRefusalOutcomes} failing=${JSON.stringify(failing(r))}`);
  console.log("   e.g. side dimension 'the Harlan plan':", JSON.stringify(side["the Harlan plan"]));
}

// R3: 4 of every 5 paired samples (both sides) stopped before the model; one exercised sample per side remains.
{
  const raw = rows();
  for (const l of raw) if ((l.part === "a" || l.part === "b") && (l.sample as number) >= 1) {
    l.status = 422; l.body = { v: 1, error: "invalid" }; l.evaluation = { modelCalled: false, code: "E_NOT_A_MARK", ms: 1 };
  }
  const r = run(raw);
  console.log(`R3 real corpus, ${raw.filter((l) => l.status === 422).length} of ${raw.filter((l) => l.part === "a" || l.part === "b").length} paired rows preflight-rejected:`,
    `ok=${r.ok} allGatesPass=${r.results.allGatesPass} complete=${r.results.complete} failing=${JSON.stringify(failing(r))}`);
}
