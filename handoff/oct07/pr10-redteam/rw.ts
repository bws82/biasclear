import { ctx, run, marks } from "./lib.ts";
const out = (name: string, r: any) => console.log((r.ok ? (r.plainerState === "kept" ? "KEPT " : "drop ") : "FAIL ") + name.padEnd(46) + (r.ok ? r.plainerState : r.code));
const HOW = (m: string) => `The words "${m}" offer agreement as the reason to accept the claim.`;
type T = [string, string, string, string, string[]]; // sentence, rule, markText, how-mark, rewrites
const sets: T[] = [
  ["Every serious economist agrees that the plan will not raise rents by 10% within two years.", "CONSENSUS_AS_EVIDENCE", "", "Every serious economist agrees", [
    "Many economists say that the plan will not raise rents by 10% within two years.",
    "Many economists say that the plan won't raise rents by 10% within two years.",
    "Many economists say that the plan will raise rents by 10% within two years.",
    "Many economists say that the plan will not lower rents by 10% within two years.",
    "Many economists say that the plan may not raise rents by 10% within two years.",
    "Many economists say that the plan will not raise rents by 10 within two years.",
    "Many economists say that the plan will not raise rents by 1% within two years.",
    "Many economists say that the plan will not raise rents by ten percent within two years.",
    "Many economists say that the plan will not raise rents by 10% within twenty years.",
    "Many economists say that the plan will not raise rents by 10% within two years!",
    "Many economists say that the plan will not raise rents by 10% within two years",
    "Many economists say that the plan will not not raise rents by 10% within two years.",
    "Many economists do not say that the plan will not raise rents by 10% within two years.",
    "Few economists say that the plan will not raise rents by 10% within two years.",
    "No economists say that the plan will not raise rents by 10% within two years.",
    "some economists say that the plan will not raise rents by 10% within two years.",
    "Some economists think that the plan will not raise rents by 10% within two years.",
    "Many economists say  that the plan will not raise rents by 10% within two years.",
    "Many economists say that the plan will not raise rents by 10% within two years.",
    "Many economists say that the plan will nоt raise rents by 10% within two years.",
    "Many economists say that the plan will not raise rents by 10٪ within two years.",
    "Many economists say that the plan will nоt raise rents by 10% within two years.",
  ]],
  ["Only a fool would vote against the plan.", "SHAME_LEVER", "", "Only a fool", [
    "Some people would vote against the plan.",
    "Some people would vote for the plan.",
    "Some people might vote against the plan.",
    "Some people vote against the plan.",
    "Nobody would vote against the plan.",
  ]],
  ["No serious scientist disputes that the vaccine is safe for children.", "DISSENT_DISMISSAL", "", "No serious scientist disputes", [
    "Some scientists say that the vaccine is safe for children.",
    "Some scientists say that the vaccine is dangerous for children.",
    "Some scientists say that the vaccine is not safe for children.",
    "Some scientists say that the vaccine isn't safe for children.",
    "Some scientists dispute that the vaccine is safe for children.",
  ]],
  ["Studies show the tax cut always raises wages for all workers.", "CLAIM_WITHOUT_CITATION", "", "Studies show", [
    "Some studies suggest the tax cut always raises wages for all workers.",
    "Some studies suggest the tax cut sometimes raises wages for all workers.",
    "Some studies suggest the tax cut always raises wages for some workers.",
    "Some studies suggest the tax cut always lowers wages for all workers.",
    "Some studies suggest the tax cut never raises wages for all workers.",
    "Some studies suggest the wages always raise tax cut for all workers.",
  ]],
  ["Any decent person can see the senator lied to voters.", "MORAL_HIGH_GROUND", "", "Any decent person can see", [
    "Some people think the senator lied to voters.",
    "Some people think voters lied to the senator.",
    "Some people think the senator did not lie to voters.",
  ]],
  ["The council has concluded that the bridge is unsafe.", "INSTITUTIONAL_POSITION_AS_SETTLED", "", "has concluded that", [
    "The council says that the bridge is unsafe.",
    "The council says that the bridge is safe.",
    "The council says that the bridge may be unsafe.",
  ]],
];
for (const [s, rule, , m, rws] of sets) {
  console.log("\n# " + s + "  marks=" + JSON.stringify(marks(s)));
  let c; try { c = ctx(s, rule); } catch (e) { console.log("  (not marked)", (e as Error).message); continue; }
  console.log("  mark=" + JSON.stringify(s.slice(c.start, c.end)));
  for (const p of rws) out(p, run(c, HOW(s.slice(c.start, c.end)), p));
}
