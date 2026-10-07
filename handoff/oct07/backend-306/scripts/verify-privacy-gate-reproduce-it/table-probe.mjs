import { readFileSync } from "node:fs";
import { modelTable } from "/tmp/claude-0/-home-user-biasclear/bb187462-b843-5453-a36d-b91a5ff093cc/scratchpad/pr10b-wt/infra/aws/model-table.mjs";
const src = readFileSync("/tmp/claude-0/-home-user-biasclear/bb187462-b843-5453-a36d-b91a5ff093cc/scratchpad/pr10b-wt/packages/explain/src/models.ts", "utf8");
for (const [name, repl] of [["empty", "[]"], ["sourceOnly", '["us-east-1"]']]) {
  const edited = src.replace(/"destinationRegions":\s*\[[^\]]*\]/, '"destinationRegions": ' + repl);
  if (edited === src) { console.log(name, "no-substitution"); continue; }
  try { modelTable(edited); console.log(name, "ACCEPTED"); } catch (e) { console.log(name, "rejected:", e.message); }
}
