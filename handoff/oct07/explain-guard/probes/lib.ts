import { bundledEngines, type Domain } from "../../fix-wt/packages/explain/src/engines.js";
import { bundledMoves } from "../../fix-wt/packages/explain/src/moves.js";
import { checkReply, type CheckContext } from "../../fix-wt/packages/explain/src/output.js";
export { buildPrompt, asData } from "../../fix-wt/packages/explain/src/prompt.js";
export { validSentence } from "../../fix-wt/packages/explain/src/request.js";
const engines = bundledEngines();
export const engine = engines.builds.get(engines.current)!;
const moves = bundledMoves();
export { moves };
export function ctx(sentence: string, ruleId: string, domain: Domain = "general"): CheckContext {
  const marks = engine.scan(sentence, domain);
  const mark = marks.find((m) => m.ruleId === ruleId);
  if (!mark) throw new Error(`not marked: ${sentence} :: ${JSON.stringify(marks)}`);
  return { mode: "how-and-plainer", sentence, start: mark.start, end: mark.end, ruleId, domain,
    moveName: moves.get(ruleId)!.name, moveShort: moves.get(ruleId)!.short, engine,
    sentenceRuleIds: new Set(marks.map((m) => m.ruleId)),
    ruleSpans: marks.filter((m) => m.ruleId === ruleId).map((m) => ({ start: m.start, end: m.end })) };
}
export function run(c: CheckContext, how: string, plainer: string | null) {
  const payload: any = { how }; if (plainer !== null) payload.plainer = plainer;
  const r: any = checkReply({ content: [{ type: "text", text: JSON.stringify(payload) }], stop_reason: "end_turn" },
    plainer === null ? { ...c, mode: "how-only" } : c);
  ((globalThis as any).__rec ??= []).push({ sentence: c.sentence, rule: c.ruleId, domain: c.domain, how, plainer, ok: r.ok, code: r.code ?? null, state: r.plainerState ?? null });
  return r;
}
export function marks(s: string, d: Domain = "general") { return engine.scan(s, d); }
import { writeFileSync } from "node:fs";
process.on("exit", () => process.env.REC_OUT && writeFileSync(process.env.REC_OUT, JSON.stringify((globalThis as any).__rec ?? [])));
