import { ctx, run, marks } from "./lib.ts";
const S = "Every serious economist agrees that the Harlan Valley plan will lower rents within two years.";
console.log(JSON.stringify(marks(S)));
const c = ctx(S, "CONSENSUS_AS_EVIDENCE");
const GOOD = 'The words "Every serious economist agrees" offer agreement as the reason to accept the forecast. The sentence does not say what evidence those economists rely on.';
console.log(run(c, GOOD, "Many economists say that the Harlan Valley plan will lower rents within two years."));
