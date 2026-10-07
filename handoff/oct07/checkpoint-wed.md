# Checkpoint · Wed Oct 7 (Claude)

**Usage:** baseline 47%. Consumed is **unverified** because this session can't read the meter. Brad's reading is requested at this checkpoint.

## Delivered

**304:** composed explanations with exact-source-or-refuse.
- `handoff/oct07/composed-304/`
- Base 2299fe1, commit 47952e1, patch sha256 `e75a9f54…a0827d`.
- 10 files.
- Tests: 101 pass (patch alone); full package 13 failures, all in Jarvis-owned free-text stubs, with the integration note applied; root 10690 passed; build scan passes.

**306:** backend review of PR #10 at 19eebb3.
- `handoff/oct07/backend-306/REPORT-306.md`, with `findings.json` and the probes in the same folder.
- Verdict: NO-GO for the integration checkpoint until the five ★ items are fixed or Brad accepts them.

**311:** PR #12 (adccb37), bounded one-file read.
- `handoff/oct07/pr12-review-311.md`
- GO, with one LOW finding.

## Confirmed findings, ranked for Thursday (injection → spending control → privacy)

| # | Area | Finding | State |
|---|---|---|---|
| 1 | Injection | Quote breakout through the displayed mark (12 confirmed, round 3) | Fixed in 304 (exact quote or refuse); Jarvis review owed |
| 2 | Injection | Free-text explanation bypasses (308 on v2, 173 earlier) | Removed by design in 304 (free text never shown); regressions kept |
| 3 | Injection/eval | ★ Preflight-rejected rows don't make a run incomplete, so injection and claim gates can pass with no injection reaching the model | Thu: fix + regression |
| 4 | Injection/eval | Refusal-parity gate misses common refusal wording | Thu |
| 5 | Spending | ★ Durable pause and debt share one transaction with the most contended item, so concurrency loses both (with 2 related MEDIUMs: conflict → permanent pause; per-event debt on the shared pause item) | Thu: fix + regression |
| 6 | Spending | ★ A definite settle cancellation → permanent service-wide pause, and a valid paid answer is discarded | Thu |
| 7 | Spending | ★ Billing-anomaly metric filter can't match stored Lambda log events, so the alarm never fires (depends on the documented AWS log envelope) | Thu: fix offline; confirm at the AWS sitting |
| 8 | Privacy/consent | ★ A deploy with a different model switches live traffic to a maker the consent doesn't name; the approval summary omits the model | Thu |
| 9 | Privacy | Consent says Explain pauses on a setting change, but traffic continues up to 15 min per warm instance; privacy drafts omit network-address processing | Thu/Sat (privacy draft) |
| 10 | Spending | LOWs: 28 s deadline vs. the timeout chain; leaked reservations; the in-flight overrun disclosure; debts not counted in headroom | Fri/Sat |
| 11 | Docs | $30 budget stop: docs contradict each other on the month-start lift | Sat |
| 12 | Tests | PR #12: encoded `javascript:`/`data:`/`vbscript:`/`srcdoc` not covered | Optional, test-only |

## Open decisions (Brad)
- Adopt composed explanations (Grok selects reviewed phrases instead of writing)?
- Evaluation question set and the 80% floor.
- Real names vs. stand-ins.
- AWS sitting.
- Protect-main.
- Merging PRs #4, #6, #8, #10, #12.

## Reviews owed
- Jarvis: independent review of 304, and later of the integration candidate.
- Claude: none outstanding.

## Next block (after Brad's meter reading)
- Thursday: the integration candidate on 19eebb3, starting with items 3, 5, 6, 7 and 8.
