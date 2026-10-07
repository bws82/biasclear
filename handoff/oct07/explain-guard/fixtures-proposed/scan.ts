import { bundledEngines } from "../fix-wt/packages/explain/src/engines.ts";
import { readFileSync } from "node:fs";
const reg = bundledEngines();
const e = reg.builds.get(reg.current)!;
const lines: string[] = JSON.parse(readFileSync(process.argv[2], "utf8"));
const out: Record<string, {ruleId:string;text:string}[]> = {};
for (const t of lines) out[t] = e.scan(t, "general").map(m => ({ ruleId: m.ruleId, text: t.slice(m.start, m.end) }));
console.log(JSON.stringify({ version: reg.current, out }));
