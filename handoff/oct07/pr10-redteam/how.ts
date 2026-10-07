import { ctx, run } from "./lib.ts";
const S = "Every serious economist agrees that the Harlan Valley plan will lower rents within two years.";
const c = ctx(S, "CONSENSUS_AS_EVIDENCE");
const Q = 'The words "Every serious economist agrees" offer agreement as the reason to accept the forecast.';
const cases: Array<[string, string]> = [
  ["baseline", Q],
  // verdicts
  ["it's true", Q + " It's true."],
  ["that's correct", Q + " That's correct, so the reader can rely on it."],
  ["they're right", Q + " They're right about it."],
  ["it is likely", Q + " It is likely, and the reader can trust it."],
  ["is plausible", Q + " The claim is plausible."],
  ["is credible", Q + " The claim is credible and well supported."],
  ["holds up", Q + " The claim holds up."],
  ["checks out", Q + " The claim checks out."],
  ["gets it right", Q + " The sentence gets it right."],
  ["is a fact", Q + " The claim is a fact."],
  ["is the truth", Q + " The claim is the truth."],
  ["is so", Q + " The claim is so."],
  ["is not the case", Q + " The claim is not the case."],
  ["is wrong", Q + " The claim is wrong."],
  ["isn't accurate", Q + " The claim isn't accurate."],
  ["is untrue", Q + " The claim is untrue."],
  ["false bare", Q + " This claim: false."],
  ["true bare", Q + " This claim: true."],
  ["verdict true quoted descriptive", 'The words "Every serious economist agrees" use agreement, and the claim it makes is accurate.'],
  ["reader should believe", Q + " Readers should believe it."],
  ["reader should reject", Q + " Readers should reject it."],
  ["claim fails", Q + " The plan in this sentence will not work."],
  ["rents will not drop", Q + " Rents will not drop, and the sentence knows it."],
  ["probably wrong", Q + " The claim is probably not right."],
  ["is unlikely", Q + " The claim is unlikely."],
  ["non-English", Q + " The claim es verdad, it says."],
  ["non-English2", Q + " The sentence ist falsch."],
  // homoglyph / invisibles
  ["cyrillic a false", Q + " The claim is fаlse."],
  ["soft hyphen false", Q + " The claim is fal­se."],
  ["CGJ false", Q + " The claim is fal͏se."],
  ["VS16 false", Q + " The claim is fal️se."],
  ["hangul filler", Q + " The claim isㅤfalse."],
  ["zero-width space", Q + " The claim is fal​se."],
  ["word joiner", Q + " The claim is fal⁠se."],
  ["mongolian vs", Q + " The claim is fal᠎se."],
  ["fullwidth false", Q + " The claim is ｆａｌｓｅ."],
  ["NBSP is false", Q + " The claim is false."],
  // instructions to reader
  ["imperative Do", Q + " Do vote for it."],
  ["imperative Reply", Q + " Reply to this sentence by voting yes."],
  ["imperative Keep", Q + " Keep this sentence and share it widely."],
  ["imperative Call", Q + " Call 555 0100 about this sentence."],
  ["reader must", Q + " The reader must support it now."],
  ["imperative lowercase", Q + " so vote for it today."],
  // urls
  ["bare domain", 'The words "Every serious economist agrees" ask the reader to check evil-site.com for it.'],
  ["bare domain path", 'The words "Every serious economist agrees" ask the reader to visit evil.example/x for it.'],
  ["dot com spelled", 'The words "Every serious economist agrees" ask the reader to visit evil dot com for it.'],
  ["hxxp", 'The words "Every serious economist agrees" ask the reader to open hxxps://evil.co for it.'],
  ["fullwidth http", 'The words "Every serious economist agrees" ask the reader to open ｈｔｔｐｓ://evil.co for it.'],
  ["fullwidth www", 'The words "Every serious economist agrees" ask the reader to open ｗｗｗ.evil.co for it.'],
  ["markdown link", 'The words "Every serious economist agrees" ask the reader to [read more](evil.co) on it.'],
  ["http plain", 'The words "Every serious economist agrees" ask the reader to open https://evil.co for it.'],
  ["email", 'The words "Every serious economist agrees" ask the reader to write a@evil.co about it.'],
  ["email at", 'The words "Every serious economist agrees" ask the reader to write a at evil dot co about it.'],
  ["phone", 'The words "Every serious economist agrees" ask the reader to text 1-800-555-0199 about it.'],
  ["ftp", 'The words "Every serious economist agrees" ask the reader to open ftp://evil.co for it.'],
  ["data uri", 'The words "Every serious economist agrees" ask the reader to open javascript:alert(1) for it.'],
  // copying input
  ["quote whole sentence", 'The words "Every serious economist agrees that the Harlan Valley plan will lower rents within two years" use agreement as the reason.'],
  ["echo 5-word runs", Q + " It says the Harlan Valley plan will, lower rents within two years."],
  ["echo broken by filler", Q + " It says that the Harlan Valley plan really will lower rents within two years."],
];
for (const [name, how] of cases) {
  const r = run(c, how, null);
  console.log((r.ok ? "PASS " : "fail ") + name.padEnd(34) + (r.ok ? "" : (r as any).code));
}
