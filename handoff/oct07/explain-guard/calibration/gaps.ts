import { ctx } from "./new/lib.ts";
import { vocabularyGaps, guardHow } from "../fix-wt/packages/explain/src/howguard.ts";
import { bundledMoves } from "../fix-wt/packages/explain/src/moves.ts";
import { readFileSync } from "node:fs";
const S = JSON.parse(readFileSync("../rt-fix/calib-sentences.json", "utf8"));
const names = [...bundledMoves().values()].map(m => m.name);
const count: Record<string, number> = {}; const other: Record<string, number> = {};
for (const a of JSON.parse(readFileSync("../rt-fix/" + (process.env.CALIB ?? "calib-A.json"), "utf8"))) {
  const s = S[a.i]; let c: any; try { c = ctx(s.sentence, s.rule, s.domain); } catch { continue; }
  const g = { sentence: s.sentence, start: c.start, end: c.end, moveName: c.moveName, moveShort: c.moveShort, otherMoveNames: names };
  const how = a.how.replace(/\s+/g, " ").trim();
  for (const w of new Set(vocabularyGaps(how, g))) count[w] = (count[w] ?? 0) + 1;
  const r = guardHow(how, g); if (r && r !== "vocabulary") { other[r] = (other[r] ?? 0) + 1; if (process.env.SHOWO) console.log(r, "|", how); }
}
console.log(Object.entries(count).sort((a, b) => b[1] - a[1]).map(([w, n]) => `${w}:${n}`).join(" "));
console.log("non-vocabulary:", other);
