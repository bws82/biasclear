// Independent re-derivation for the eval-gates findings (find-the-guard-elsewhere).
// Uses the real handler with the repo's in-memory fakes to produce app-shaped rows,
// then feeds them to report(). Read-only against the checkout.
import { readFileSync } from "node:fs";
import { evaluationRequests, report, refusalLike, classifySample, sampleOf, validAnswer, requestFor,
  type Fixtures, type HumanReview, type RawLine } from "../../pr10b-wt/packages/explain/ops/ops.ts";
import { harness, modelReply, EVAL_KEY, STUB_MODELS } from "../../pr10b-wt/packages/explain/test/helpers.ts";
import { MODELS } from "../../pr10b-wt/packages/explain/src/models.ts";

const root = new URL("../../pr10b-wt/packages/explain/", import.meta.url);
const f = JSON.parse(readFileSync(new URL("eval/fixtures.json", root), "utf8")) as Fixtures;
const planned = evaluationRequests(f);
const MODEL_ID = Object.keys(MODELS)[0]!;
const MODEL = MODELS[MODEL_ID]!.displayName;

// ---- Real handler rows -------------------------------------------------------
async function appRow(request: Record<string, unknown>, script: any, faultSettle = false) {
  const h = harness();
  h.aws.model = script;
  if (faultSettle) h.aws.table.fault = (op, payload) => op === "TransactWriteItems" && JSON.stringify(payload).includes(":settled") ? "network" : undefined;
  return await h.handler({ explainEvaluation: 1, key: EVAL_KEY, request }) as { status: number; body: Record<string, unknown>; evaluation: Record<string, unknown> };
}

const goodHow = (req: Record<string, unknown>) => {
  const s = req.sentence as string; const mark = s.slice(req.start as number, req.end as number);
  return `The words "${mark}" frame the claim for the reader. The sentence gives no further reason for that framing.`;
};

const c24 = planned.at(-1)!;
console.log("last planned row:", c24.id, c24.part, c24.sample);

// Sanity: the harness answers an ordinary call (proves the eval key/config path works).
const okRow = await appRow(c24.request, () => ({ status: 200, json: modelReply({ how: goodHow(c24.request), plainer: null, inTok: 100, outTok: 40 }) }));
console.log("APP ok row:", okRow.status, JSON.stringify(okRow.body).slice(0, 120));
console.log("  validAnswer(body, rule) =", okRow.status === 200 ? validAnswer(okRow.body, String(c24.request.rule)) : "n/a",
  " body.rules === request.rules:", okRow.body.rules === c24.request.rules);
console.log("  evaluation keys:", Object.keys(okRow.evaluation).sort().join(","));
console.log("  F7 check: actualMicros", okRow.evaluation.actualMicros, "<= reservedMicros", okRow.evaluation.reservedMicros, "flag", okRow.evaluation.billedBoundViolated);

// F3: app rows with model called but odd provider content always carry inconsistent-or-missing flags the gate counts.
for (const [label, script] of [
  ["content not array", () => ({ status: 200, json: modelReply({ content: "nope", inTok: 100, outTok: 40 }) })],
  ["empty content", () => ({ status: 200, json: modelReply({ content: [], inTok: 100, outTok: 40 }) })],
  ["throttled", () => ({ status: 429, errorType: "ThrottlingException", json: {} })],
  ["no usage", () => ({ status: 200, json: modelReply({ usage: null }) })],
] as const) {
  const r = await appRow(c24.request, script as any);
  const s = sampleOf({ id: c24.id, part: c24.part, sample: c24.sample, status: r.status, body: r.body, evaluation: r.evaluation });
  console.log(`F3 app row [${label}]: status=${r.status} code=${r.evaluation.code} modelCalled=${s.modelCalled} providerText=${JSON.stringify(s.providerText)} chars=${s.providerTextChars} truncated=${s.providerTextTruncated} stop=${s.providerStopReason} classify=${classifySample(s)}`);
}

// F6: real E_SETTLE row with refusal text.
const settleRow = await appRow(c24.request, () => ({ status: 200, json: modelReply({ text: "Sorry, I can't help with that.", inTok: 100, outTok: 40 }) }), true);
const settleSample = sampleOf({ ...settleRow, id: c24.id, part: c24.part, sample: c24.sample });
console.log(`F6 app E_SETTLE row: status=${settleRow.status} body=${JSON.stringify(settleRow.body)} code=${settleRow.evaluation.code} pausePersisted=${settleRow.evaluation.pausePersisted} classify=${classifySample(settleSample)}`);
const settleRowPlain = await appRow(c24.request, () => ({ status: 200, json: modelReply({ text: '{"how":"x"}', inTok: 100, outTok: 40 }) }), true);
console.log(`F6 app E_SETTLE row, non-refusal text: code=${settleRowPlain.evaluation.code} classify=${classifySample(sampleOf({ ...settleRowPlain }))}`);

// F2: real handler, curly-apostrophe refusal text.
for (const t of ["I’m sorry, but I can’t help with content about this group.", "I'm sorry, but I can't help with content about this group.", "I'm not able to help with that.", "I can’t assist with that."]) {
  const r = await appRow(c24.request, () => ({ status: 200, json: modelReply({ text: t, inTok: 100, outTok: 40 }) }));
  const s = sampleOf({ ...r });
  console.log(`F2 app row text=${JSON.stringify(t)} -> status=${r.status} code=${r.evaluation.code} refusalLike=${refusalLike(s)} classify=${classifySample(s)}`);
}

// Real preflight rows (rules drift / not a mark).
const driftReq = { ...c24.request, rules: "0.0.0-not-deployed" };
const drift = await appRow(driftReq, () => { throw new Error("model must not be called"); });
console.log(`F1 app drift row: status=${drift.status} code=${drift.evaluation.code} modelCalled=${drift.evaluation.modelCalled} classify=${classifySample(sampleOf({ ...drift }))}`);
const nam = await appRow({ ...c24.request, start: 0, end: 1 }, () => { throw new Error("model must not be called"); });
console.log(`F1 app not-a-mark row: status=${nam.status} code=${nam.evaluation.code} classify=${classifySample(sampleOf({ ...nam }))}`);

// ---- Report-level checks with app-shaped rows -----------------------------------
const GOOD = "The sentence asks for agreement as a reason.";
const goodText = JSON.stringify({ how: GOOD });
const evalOk = () => ({ modelCalled: true, providerStopReason: "end_turn", providerText: goodText, providerTextTruncated: false,
  providerTextChars: goodText.length, inTok: 10, outTok: 20, inputBoundTokens: 500, outputBoundTokens: 400,
  billedBoundViolated: false, actualMicros: 50, micros: 50, reservedMicros: 100, ms: 5, code: undefined });
const rows = (): RawLine[] => planned.map((p) => ({ id: p.id, part: p.part, sample: p.sample, status: 200,
  body: { v: 1, rule: p.request.rule, how: GOOD, plainer: null, model: MODEL, rules: p.request.rules }, evaluation: evalOk() }));
const preflightOf = (l: RawLine, ev: Record<string, unknown>, status: number, body: Record<string, unknown>) => { l.status = status; l.body = body; l.evaluation = ev; };
function run(raw: RawLine[], opts: { model?: boolean; reviewModel?: string | null; fx?: Fixtures } = {}) {
  const fx = opts.fx ?? f;
  const pl = evaluationRequests(fx);
  const base = opts.model === false ? {} : { model: MODEL, modelId: MODEL_ID };
  const pending = report(fx, pl.length, raw, base);
  const review: HumanReview = { fixtureHash: String(pending.results.fixtureHash), rawHash: String(pending.results.rawHash),
    model: (opts.reviewModel === null ? undefined : opts.reviewModel ?? MODEL_ID) as string, reviewer: "Independent", answers: {} };
  if (opts.reviewModel === null) delete (review as Partial<HumanReview>).model;
  for (const p of pl) review.answers[`${p.id}/${p.part}/${p.sample}`] = { injection: "safe", rewrite: "preserved", useful: true };
  return { pending, final: report(fx, pl.length, raw, { ...base, review, plannedRequests: pl }) };
}
const failing = (r: ReturnType<typeof report>) => Object.entries(r.results.gates as Record<string, boolean>).filter(([, v]) => !v).map(([k]) => k);

{ // baseline
  const { pending, final } = run(rows());
  console.log(`BASE: CI-style (no review) ok=${pending.ok} failing=${JSON.stringify(failing(pending))}; with review ok=${final.ok}`);
}
{ // F1: injection+rewrite rows preflight, using the app's real drift row shape
  const raw = rows();
  for (const l of raw) if (l.part === "i" || l.part === "r") preflightOf(l, drift.evaluation, drift.status, drift.body);
  const { pending, final } = run(raw);
  console.log(`F1a inj+rew preflight (E_RULES_VERSION shape): CI ok=${pending.ok} failing=${JSON.stringify(failing(pending))}; reviewed ok=${final.ok} complete=${final.results.complete} preflight=${final.results.preflightRejected} failing=${JSON.stringify(failing(final))}`);
  const md = final.markdown.split("\n").filter((x) => /Preflight|All \d+ planned|Written gates/.test(x));
  console.log("   markdown:", JSON.stringify(md));
}
{ // F1: full drift on every row (rules version unknown everywhere)
  const raw = rows();
  for (const l of raw) preflightOf(l, drift.evaluation, drift.status, drift.body);
  const { final } = run(raw);
  console.log(`F1b full rules drift: reviewed ok=${final.ok} failing=${JSON.stringify(failing(final))}`);
}
{ // F1: 4 of 5 paired samples preflight
  const raw = rows();
  for (const l of raw) if ((l.part === "a" || l.part === "b") && (l.sample as number) >= 1) preflightOf(l, nam.evaluation, nam.status, nam.body);
  const { final } = run(raw);
  console.log(`F1c 4/5 paired samples preflight: reviewed ok=${final.ok} failing=${JSON.stringify(failing(final))}`);
}
{ // F2: one coincident sample, curly vs ascii
  for (const text of ["I’m sorry, but I can’t help with content about this group.", "I'm sorry, but I can't help with content about this group."]) {
    const raw = rows();
    const a = raw.find((l) => l.id === f.pairs[0]!.id && l.part === "a" && l.sample === 0)!;
    const b = raw.find((l) => l.id === f.pairs[0]!.id && l.part === "b" && l.sample === 0)!;
    a.status = 502; a.body = { v: 1, error: "no_answer" }; a.evaluation = { ...evalOk(), code: "E_OUT_SHAPE", providerText: text, providerTextChars: text.length };
    const other = '{"how":"The words say this side is right."}';
    b.status = 502; b.body = { v: 1, error: "no_answer" }; b.evaluation = { ...evalOk(), code: "E_OUT_VERDICT", providerText: other, providerTextChars: other.length };
    const { final } = run(raw);
    console.log(`F2 coincident one-sided refusal ${text.includes("’") ? "CURLY" : "ASCII"}: ok=${final.ok} unmatchedRefusal=${final.results.unmatchedRefusalOutcomes} failing=${JSON.stringify(failing(final))}`);
  }
  // non-coincident: other side answered
  const raw = rows();
  const a = raw.find((l) => l.id === f.pairs[0]!.id && l.part === "a" && l.sample === 0)!;
  const text = "I’m sorry, but I can’t help with content about this group.";
  a.status = 502; a.body = { v: 1, error: "no_answer" }; a.evaluation = { ...evalOk(), code: "E_OUT_SHAPE", providerText: text, providerTextChars: text.length };
  const { final } = run(raw);
  console.log(`F2 non-coincident curly refusal (other side answered): ok=${final.ok} failing=${JSON.stringify(failing(final))}`);
}
{ // F4: no --model, review without model key
  const raw = rows();
  for (const l of raw) (l.body as Record<string, unknown>).model = "Some unreviewed model";
  const r1 = run(raw, { model: false, reviewModel: null });
  const r2 = run(raw, { model: true, reviewModel: null });
  const r3 = run(raw, { model: false, reviewModel: MODEL_ID });
  console.log(`F4 no --model + review without model: ok=${r1.final.ok} reviewBound=${r1.final.results.reviewBound}; with --model: ok=${r2.final.ok}; no --model but review.model set: ok=${r3.final.ok} reviewBound=${r3.final.results.reviewBound}`);
}
{ // F5: tiny fixture; DRAFT corpus
  const tiny: Fixtures = { samples: { pairs: 1, injections: 0, rewrites: 0, controls: 1 }, pairs: [f.pairs[0]!], injections: [f.injections[0]!], rewrites: [], controls: [f.controls!.find((c) => c.set === "heldout")!] };
  const pl = evaluationRequests(tiny);
  const raw: RawLine[] = pl.map((p) => ({ id: p.id, part: p.part, sample: p.sample, status: 200, body: { v: 1, rule: p.request.rule, how: GOOD, plainer: null, model: MODEL, rules: p.request.rules }, evaluation: evalOk() }));
  const { final } = run(raw, { fx: tiny });
  console.log(`F5 tiny fixture planned=${pl.length}: ok=${final.ok}; DRAFT about=${JSON.stringify((f.about ?? "").slice(0, 40))}`);
  const { final: full } = run(rows());
  console.log(`F5 DRAFT corpus all accepted+reviewed: ok=${full.ok}`);
}
{ // F6: real E_SETTLE row as the last planned row
  const raw = rows();
  const last = raw.at(-1)!;
  last.status = settleRow.status; last.body = settleRow.body; last.evaluation = settleRow.evaluation;
  const { final } = run(raw);
  console.log(`F6 last row real E_SETTLE+refusal text: ok=${final.ok} complete=${final.results.complete} serviceBlocked=${final.results.serviceBlocked} unknown=${final.results.unknown} failing=${JSON.stringify(failing(final))}`);
  const raw2 = rows();
  const last2 = raw2.at(-1)!;
  last2.status = settleRowPlain.status; last2.body = settleRowPlain.body; last2.evaluation = settleRowPlain.evaluation;
  const { final: f2 } = run(raw2);
  console.log(`F6 last row real E_SETTLE, non-refusal text: ok=${f2.ok} failing=${JSON.stringify(failing(f2))}`);
}
console.log("STUB_MODELS keys", Object.keys(STUB_MODELS).join(","), "MODEL_ID", MODEL_ID);
// requestFor import retained for parity with fixtures generation
void requestFor;
