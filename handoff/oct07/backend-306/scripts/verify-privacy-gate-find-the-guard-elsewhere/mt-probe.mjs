import { readFileSync } from "node:fs";
const wt = process.argv[2];
const { modelTable } = await import(`${wt}/infra/aws/model-table.mjs`);
const src = readFileSync(`${wt}/packages/explain/src/models.ts`, "utf8");
const emptied = src.replace(/"destinationRegions": \[\s*"us-east-1",\s*"us-east-2",\s*"us-west-2"\s*\]/, '"destinationRegions": []');
console.log("edited:", emptied !== src);
try { modelTable(emptied); console.log("accepted"); } catch (e) { console.log("rejected:", e.message); }
try { modelTable(src); console.log("original accepted"); } catch (e) { console.log("orig rejected", e.message); }
