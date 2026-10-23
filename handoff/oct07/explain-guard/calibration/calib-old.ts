import { ctx, run } from "./old/lib.ts";
import { readFileSync } from "node:fs";
const S = JSON.parse(readFileSync("../rt-fix/calib-sentences.json", "utf8"));
for (const f of ["calib-A.json", "calib-B.json"]) { let n = 0, ok = 0;
  for (const a of JSON.parse(readFileSync("../rt-fix/" + f, "utf8"))) { const s = S[a.i]; let c: any; try { c = ctx(s.sentence, s.rule, s.domain); } catch { continue; } n++; if ((run(c, a.how, null) as any).ok) ok++; }
  console.log(f, `original checker accepted ${ok}/${n}`); }
