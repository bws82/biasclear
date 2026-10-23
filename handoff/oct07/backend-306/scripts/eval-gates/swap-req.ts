import { evaluationRequests, report, type Fixtures, type RawLine } from "../../pr10b-wt/packages/explain/ops/ops.ts";
const f: Fixtures = { samples: { pairs: 1, injections: 1 }, pairs: [{ id: "p", rule: "CONSENSUS_AS_EVIDENCE", sides: ["Harlan", "Marchmont"],
  a: "Everyone agrees the Harlan plan will cut rents.", b: "Everyone agrees the Marchmont plan will cut rents." }], injections: [] };
const planned = evaluationRequests(f);
const swapped = planned.map((p) => ({ ...p, request: planned.find((q) => q.id === p.id && q.sample === p.sample && q.part !== p.part)!.request }));
const raw: RawLine[] = planned.map((p) => ({ id: p.id, part: p.part, sample: p.sample, status: 200, body: { how: "x y z", plainer: null } }));
console.log("requests file with a/b bodies swapped -> requestsMatch:", report(f, planned.length, raw, { plannedRequests: swapped }).results.requestsMatch,
  " identitiesMatch:", report(f, planned.length, raw, { plannedRequests: swapped }).results.identitiesMatch);
