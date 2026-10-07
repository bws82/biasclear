import { harness, modelReply, EVAL_KEY, requestBody } from "../../pr10b-wt/packages/explain/test/helpers.ts";
import { validAnswer, sampleOf, report } from "../../pr10b-wt/packages/explain/ops/ops.ts";
const h = harness();
const req = requestBody();
const r = await h.handler({ explainEvaluation: 1, key: EVAL_KEY, request: req }) as any;
console.log("F8 app 200:", r.status, "validAnswer:", validAnswer(r.body, String(req.rule)), "rules echo:", r.body.rules === req.rules, "keys:", Object.keys(r.body).sort().join(","));
const s = sampleOf(r);
console.log("F3/F7 200 metadata:", JSON.stringify({ mc: s.modelCalled, stop: s.providerStopReason, chars: s.providerTextChars, len: s.providerText?.length, tr: s.providerTextTruncated, inTok: s.inTok, outTok: s.outTok, inB: s.inputBoundTokens, outB: s.outputBoundTokens, act: s.actualMicros, res: s.reservedMicros, flag: s.billedBoundViolated }));
// F7: over-bound tokens -> app flags and pauses
const h2 = harness(); h2.aws.model = () => ({ status: 200, json: modelReply({ inTok: 999999, outTok: 10 }) });
const r2 = await h2.handler({ explainEvaluation: 1, key: EVAL_KEY, request: req }) as any;
console.log("F7 over-bound:", r2.status, r2.evaluation.code, "flag", r2.evaluation.billedBoundViolated, "actual", r2.evaluation.actualMicros, "reserved", r2.evaluation.reservedMicros);
