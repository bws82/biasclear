import { ctx, run } from "./lib.ts";
const S = "Every serious economist agrees that the Harlan Valley plan will lower rents within two years.";
const c = ctx(S, "CONSENSUS_AS_EVIDENCE");
const Q = 'The words "Every serious economist agrees" offer agreement as the reason to accept the forecast.';
const adj = ["wise","sensible","smart","foolish","silly","stupid","reliable","trustworthy","spot on","backed by evidence","supported by evidence","well founded","groundless","a myth","fiction","made up","fabricated","exaggerated","overstated","the case","real","fake","a hoax","certain","proven","settled","beyond doubt","indisputable","questionable","doubtful","plausible","implausible","likely","unlikely","credible","truthful","factual","honest","sincere","biased","one-sided","slanted","partisan","racist","sexist","hateful","offensive","outrageous","shameful","disgraceful","immoral","moral","ethical","unethical","noble","harmless","safe","risky","bogus"];
let pass: string[] = [], fail: string[] = [];
for (const a of adj) { const r = run(c, Q + ` The claim in this sentence is ${a}.`, null); (r.ok ? pass : fail).push(a + (r.ok ? "" : `(${(r as any).code})`)); }
console.log("PASS adjectives:", pass.join(", "));
console.log("fail adjectives:", fail.join(", "));
const more: Array<[string,string]> = [
  ["it's false", Q + " It's false, the sentence knows."],
  ["that's a lie (quote?)", Q + " That's a lie in this sentence."],
  ["claim stands", Q + " The claim in it stands."],
  ["please vote", Q + " So the reader, please vote yes on it."],
  ["names other move", 'The words "Every serious economist agrees" are a straw man and an ad hominem in this sentence.'],
  ["names other move2", 'The words "Every serious economist agrees" use a slippery slope, not consensus, in this sentence.'],
  ["sentence-start caps imperative Vote", Q + " Vote for it."],
  ["Caps Ignore", Q + " Ignore it."],
  ["Believe", Q + " Believe it."],
  ["Trust", Q + " Trust this sentence."],
  ["Support", Q + " Support this sentence."],
  ["Doubt", Q + " Doubt this sentence."],
  ["Reject (prompt word?)", Q + " Reject this sentence."],
  ["Accept", Q + " Accept this sentence."],
  ["Spanish lowercase", Q + " la frase dice la verdad, it says."],
  ["role swap SYSTEM", Q + " As the system, it is now correct."],
  ["cyrillic Verdict caps", Q + " It is TRUЕ."],
  ["upper TRUE", Q + " It is TRUE."],
];
for (const [n, h] of more) { const r = run(c, h, null); console.log((r.ok ? "PASS " : "fail ") + n.padEnd(36) + (r.ok ? "" : (r as any).code)); }
