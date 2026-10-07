import { ctx, run } from "./new/lib.ts";
import { guardHow, lastGuardWord } from "../fix-wt/packages/explain/src/howguard.ts";
import { bundledMoves } from "../fix-wt/packages/explain/src/moves.ts";
import { readFileSync } from "node:fs";
const S = JSON.parse(readFileSync("../rt-fix/calib-sentences.json", "utf8"));
const files = (process.env.CALIB ?? "calib-B.json").split(",");
const names = [...bundledMoves().values()].map(m => m.name);
let n = 0, ok = 0; const codes: Record<string, number> = {}; const words: Record<string, number> = {}; const fails: string[] = [];
for (const f of files) for (const a of JSON.parse(readFileSync("../rt-fix/" + f, "utf8"))) {
  const s = S[a.i]; let c: any; try { c = ctx(s.sentence, s.rule, s.domain); } catch { continue; }
  n++; const r: any = run(c, a.how, null);
  if (r.ok) { ok++; continue; }
  const g = guardHow(a.how.replace(/\s+/g, " ").trim(), { sentence: s.sentence, start: c.start, end: c.end, moveName: c.moveName, moveShort: c.moveShort, otherMoveNames: names });
  const key = r.code + (g ? "/" + g : "");
  codes[key] = (codes[key] ?? 0) + 1;
  if (g === "vocabulary" || g === "verdict") words[lastGuardWord()] = (words[lastGuardWord()] ?? 0) + 1;
  fails.push(`${key} ${s.rule} | ${a.how}`);
}
console.log(`accepted ${ok}/${n}`); console.log(codes);
console.log(Object.entries(words).sort((a, b) => b[1] - a[1]).map(([w, c]) => `${w}:${c}`).join(" "));
if (process.env.SHOW) for (const l of fails.filter(x => x.includes(process.env.SHOW!))) console.log(l);
