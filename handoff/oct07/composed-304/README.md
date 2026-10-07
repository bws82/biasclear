# 304 · Composed explanations (checker packet, prototype)

**Status:** pinned patch for Jarvis's independent review. It is not published to PR #10 and not self-cleared. **Adopting it is Brad's decision**: Grok would select reviewed phrases instead of writing the explanation.

| | |
|---|---|
| Base | `2299fe1` (PR #10 original head) |
| Commit | `47952e1e91d72ceac2db36a6533f59964e493c15` (author BiasClear) |
| Patch | `0001-explain-composed-explanations-304.patch` · sha256 `e75a9f54215524df15fe1d389917b0cd35ba95ed4bf5c7bc416fa90643a0827d` |
| Applies | cleanly on 2299fe1 (`git apply --check`) |

## Files (owned paths only)

- `packages/explain/src/compose.ts` (new)
- `packages/explain/data/explain-phrases.json` (new: 43 moves, 4–6 "does" and 4–8 "unsaid" each)
- `packages/explain/src/output.ts`
- `packages/explain/src/prompt.ts`
- `packages/explain/test/output.test.ts`
- `packages/explain/test/compose.test.ts` (new)
- `packages/explain/test/prompt.test.ts`
- `packages/explain/test/fixtures/redteam-bypasses.json` (173 attacks)
- `packages/explain/test/fixtures/redteam-r2.json` (308 attacks)
- `packages/explain/test/fixtures/redteam-r3.json` (28 attacks)

`howguard.ts` and the 301 packet are superseded and not included. Helpers and call sites are not touched here; they are covered in `integration-note.patch` and the section below.

## What it does

The model replies `{"does":[ids],"unsaid":[ids][,"plainer":"…"]}`. The ids must come from the engine-verified rule's reviewed entries. The server writes the explanation:

    The words “<exact mark>” <does1>[, and <does2>]. The sentence does not say <a, b or c>.

A one-word mark gives "The word" and the -s verb.

**Exact source or refuse (Jarvis's correction, 307/309):**
- The mark is the exact verified span, quoted character for character between curly quotes. Nothing is clipped, stripped, cleaned or reordered.
- The sentence's own straight scare quotes (`"improved"`, `The so-called 'experts'`) may stand inside, as whole pairs around words.
- An apostrophe after a letter is kept (`don't`, `teachers'`).
- These refuse the reply with E_OUT_PLAIN_TEXT, checked on the raw text and on its NFKC form:
  - any other quotation mark or prime (full-width and look-alike forms included);
  - a sentence end or ellipsis (including U+2024 and U+FF0E);
  - a control, format or bidirectional character, or a line break;
  - any whitespace other than single spaces;
  - the product's name.
- The round-3 breakout (`Either we stop him" — BiasClear confirms … — "now or`) is now refused. Before, it rendered.

**Limits and word-count accounting:**
- Unchanged from base: 400 characters, 60 words and 3 sentences, counted on the whole explanation as shown, mark included. The frame-only count from my earlier draft is dropped.
- `pickLimits(rule, mark)` gives the most picks for which every choice fits: 2+3, then 1+3, 1+2, 1+1, 1+0. It tries the longest phrases by both words and characters.
- The prompt states the same numbers ("Note: give one or two "does" ids and up to three "unsaid" ids.").
- A choice over the limits, or a mark too long for any choice, gets E_OUT_HOW. Nothing is shortened.
- Tests:
  - every choice within the limits is rendered and measured, for every move and for marks of 1–30 words;
  - with an 8-word mark, every move allows at least 1 "does" and 2 "unsaid".

**Other checks:**
- Keys must be exactly `does,unsaid[,plainer]`. These are all refused: unknown, other-rule, repeated or extra ids, extra keys, wrong types, and free text.
- Plain-text (address and contact), name, side and brand checks still run on the composed text, quoted mark included, as a backstop.
- The rewrite ("plainer") checks are unchanged: length, names, sides, brand, verdicts, same sentence, 11/11b/12.
- `buildPrompt(mode, move, sentence, start, end, ruleId)` takes the engine-verified rule id. It is required, never inferred from a display name, and the call throws for a rule with no reviewed phrases.

## Tests

| Run | Result |
|---|---|
| `vitest` output/compose/prompt, patch alone | **101 passed** |
| Full explain package, patch alone | 54 failed / 312 passed. All failures come from Jarvis-owned call sites that don't pass the rule id yet (see note). |
| Full package with `integration-note.patch` applied | **13 failed / 353 passed**. All 13 are in Jarvis-owned tests that still send free-text `how` stubs; listed below. |
| `tsc` | clean except the 4 call sites in the note |
| `node scripts/build.mjs` (network-word scan) | passes; zip sha256 `f6a85c17…4fe4b69c` |
| Root `pytest tests` | **10690 passed, 20 xfailed** |

## Evidence (offline: no AWS, no paid model calls)

**Why free text was dropped:**
- v2 controlled grammar had 308 confirmed bypasses.
- About 10% of honest answers were accepted.

**Composed, before the exact-quote change:**
- Three Claude chooser runs: 86/86 accepted after the bank fix.
- Two judges, held-out set: accurate 80/84 and 83/84; useful 83/86; safe 84/84.
- `evidence/composed-eval-judges.json`

**Round-3 red team:**
- 12 confirmed quote breakouts through the mark.
- All 28 attack cases are regressions now. Every one is refused, or shows exactly one curly quotation whose text equals the source span, followed only by reviewed phrases.

**Recorded choices re-judged under these rules:** `evidence/recorded-*.jsonl`

| Chooser | Accepted |
|---|---|
| A | 72/86 |
| B | 71/86 |
| H | 71/86 |

- 14 prompts have marks long enough that only 1 "does" fits (`evidence/pick-limits-86.jsonl`). The recorded choices were made under the old 2+3 instruction, so they are over the new limits.
- One prompt (i=31) cites `u8`, which no longer exists after the FEAR_URGENCY renumbering. The checker refuses it correctly.

**Simulation, not a fresh chooser run:** keeping each chooser's first "does" pick on those 14 gives **86/86, 85/86, 85/86**. The one refusal is the stale id. See `evidence/sim-one-does-*.jsonl`.

The `MEDIA_SELECTIVE_QUOTATION` marks (`"improved"`, `the "fresh"`) are quoted whole now.

## Limits of the evidence

- The calibration sentences are authored. They are not a human holdout.
- Choosers and judges were Claude subagents, not the production model. Relevance depends on the model.
- A mismatched bank version can't happen inside one build, because the prompt and the checker read the same bundled bank. But a bank edit invalidates recorded ids (i=31 above). Evaluation should record the bank's hash with every raw selection.
- The legacy holdout is not a usefulness test for this protocol. Fresh, protocol-appropriate controls still need to be frozen.

## Integration note (separate: Jarvis-owned files)

`integration-note.patch` applies on 2299fe1. It covers:
- `src/app.ts:285` and `eval/dry-run.ts:64`: pass the engine-verified `req.rule` as the sixth `buildPrompt` argument.
- `test/handler.test.ts:375,474`: pass the rule id the same way.
- `test/helpers.ts`: `GOOD_CHOICE = {does:["d1"], unsaid:["u1","u2"]}`, `modelReply` sends that slot JSON, and `GOOD_HOW` is the composed text with curly quotes.

Test expectations still to update (13). Each sends a free-text `how`, which is now E_OUT_SHAPE by design:
- handler: the legal-domain pass; the "obeyed" injection cases (HTML, link, new name, poem ×2, product voice, verdict); too long; the code fence; the raw reply carrying the sentence words; the tags-as-data check.
- nolog: the canary success path.
- eval-dry-run: stubs should return slot JSON.

Recommended at integration:
- Pre-check `quotable(mark)` and `pickLimits(rule, mark)` in app.ts before the model call. An unquotable or too-long mark can then be refused without spending.
- Record raw selections (`does`/`unsaid` ids plus bank hash) separately from the displayed `how` in evaluation.
- Keep the refusal, truncation and missing-evidence categories distinct.

## Open decisions and reviews owed

- **Brad:** adopt composed explanations (Grok selects instead of writes)? The prototype is not adopted until he decides.
- **Jarvis:** independent review of this packet. Claude does not self-clear.
- All three live model rows stay blocked on the input-framing and Converse reasoning-accounting proof.
