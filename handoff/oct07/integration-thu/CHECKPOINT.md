# Checkpoint · Explain integration candidate (Claude, local session)

2026-10-07 13:57:22 CDT, system clock; updated 14:02:49 CDT with 0009 and 0010. Brad present: yes (he relayed Jarvis's work order in this chat). No live calls: no AWS, no paid model call, no merge, deploy, model switch, settings or site change. Not published to PR #10; Jarvis's independent review is owed.

## Candidate

| | |
|---|---|
| Checkout | `/Users/brads/Documents/New project/biasclear-claude-thu-integration-2026-10-07` (its own clone of `biasclear/biasclear`) |
| Branch | `claude/explain-integration-thu` (local only) |
| Parent | `19eebb338ad5676075c4ab5a971eec6d379ef1bc` (PR #10 head) |
| Head | `089bcdb118b56383bd4f79ce53bb1392b5db23a5` (the five ★ fixes end at `3c6cdd7`) |
| Tree | `3f3fe14cf0a9c08ce2c75e564c743ff33cf51c1e` |
| Patches | `patches/0001`–`0010`, hashes in `SHA256SUMS` |

Replay check: `git am patches/*.patch` on a fresh `19eebb3` worktree gives the same tree, `3f3fe14c`.

35 files changed, 6,488 insertions and 759 deletions. Most of that is 304's phrase bank and red-team fixtures.

## Commits, finding → fix → test

| # | Commit | What | Regression (fails on the old code) |
|---|---|---|---|
| 0001 | `c0de9d6` | 304 patch, unchanged (`git am`; sha256 `e75a9f54…a0827d`) | 304's own tests: compose, output, prompt |
| 0002 | `f9d1096` | 304 integration, ported by hand to 19eebb3: the rule id goes to `buildPrompt`; a `quotable`/`pickLimits` pre-check runs before any spend; slot-JSON stubs and tests; injected answers are refused as free text (E_OUT_SHAPE) and as fake ids (E_OUT_HOW) | `handler.test.ts` "refuses a mark the server can't quote exactly…" (no table or model call); a mutation that skips the pre-check fails it |
| 0003 | `dd46392` | **306 ★ a**: a planned row that never reached the model makes the run incomplete. The exception is an injection the fixtures expect to be refused at the door, which fails the run if it reaches the model. New `exercised` gate and counts; the pre-check codes count as door refusals | 4 cases in `evaluation-report.test.ts`; 4 mutations caught. The reviewer's real-corpus probes now fail: R1 (81 rows at the door) and R3 (784 of 980) |
| 0004 | `d93f76d` | 304: `bankHash` is recorded with each raw selection, separate from the displayed text | handler and report tests |
| 0005 | `da777eb` | **306 ★ b**: the debt row is written first (a unique key), then the shared pause, each as its own overwrite, retried 4 times with read-back. A breach settlement commits its own debt row, not the shared pause, and `pausePersisted` is now honest on that path | `contention.test.ts` with `conflicts.ts` (DynamoDB's conflict rule, adapted from the 306 harness): 4 cases fail on the old code; 2 mutations caught |
| 0006 | `a2a46a0` | **306 ★ c**: a definite settle or reserve rejection (a conflict or throttling, nothing written) is retried up to 3 times. The event's `#s = :reserved` condition prevents a double charge. Uncertain failures still pause | 4 cases fail on the old code; 2 guards (an uncertain failure is sent once; a lost reply isn't applied twice); 3 mutations caught |
| 0007 | `04acb79` | **306 ★ d**: the filter now matches words (`?overrun ?billedBoundViolated ?pausePersisted ?E_SETTLE`), because Lambda's JSON format stores the line inside a `message` string. The README now says the alarm is unproven until the AWS sitting | `billing-filter.test.ts` runs the handler's real anomaly lines in the JSON envelope and Text form; `test_templates.py` uses fixture lines. Both fail with the old pattern |
| 0008 | `3c6cdd7` | **306 ★ e**: deploy stops if Explain is on with a different model. While the site's `explain.json` has `api` set, deploy, resume and evaluate stop before sign-in on a model the published consent doesn't name. The summary names the model and its maker, and the workflow passes `MODEL` to the summary | 5 cases in `test_scripts.py` fail on the old scripts, including the reviewer's exact on/Grok → deploy Sonnet → restore on sequence; 2 guards |
| 0009 | `d81dcfb` | 306 follow-up, refusal parity: curly apostrophes are folded; an apology, "unfortunately" or a first-person refusal anywhere in the first sentence counts; fenced JSON is unwrapped; a phrase selection is never a refusal | `evaluation-report.test.ts`: the 306 S2a wordings are refusals; ordinary answers are not; a one-sided curly refusal fails `refusalParity`. 2 tests fail on the old detector; removing the folding is caught. eval:dry still 0 refusals |
| 0010 | `089bcdb` | 306 follow-up, privacy and consent **drafts only**: "stops within 15 minutes" (each instance rechecks every 15 min); the network address is disclosed (salted daily hash, a count only, never stored or logged, key expires after two days); PRIVACY-DRAFTS.md regenerated | `privacy.test.ts` holds the copy to `SETTINGS_INTERVAL_MS` and `SALT_TTL_MS`; fails on the old generator |

## Commands and results (this Mac)

- `npm test` in `packages/explain` (typecheck, build, vitest): **462 passed**, 21 files. The 306 report counted 519 at 19eebb3 under the older test layout; 304 replaces the free-text checks, so the counts aren't comparable.
- `npm run eval:dry` (Node 22.23.3): 3,246 stub calls, **0 network attempts**, every call reserved first, $0. All three models are complete, with `notExercised` 0 and wiring passing. Verdict probes were rejected 9/9, unsafe rewrites dropped 6/6 and safe rewrites kept 12/12.
- `pytest infra/aws` (with cfn-lint and ShellCheck 0.11.0): **110 passed**.
- `cfn-lint infra/aws/explain.yaml infra/aws/setup.yaml`: clean. `node infra/aws/model-table.mjs --check`: matches.
- Not run: root `pytest tests` and the site tests. Neither the Python engine, the rules nor the site changed.

## Not proven here

- Real DynamoDB conflict, throttle and retry behaviour. `conflicts.ts` follows AWS's documented rule; it is not AWS.
- Whether the CloudWatch term filter matches real stored events. The Lambda envelope is modelled offline; this is for the AWS sitting.
- Model quality. Every model row stays blocked, and the 304 choosers and judges were Claude, not the production model.
- The consent binding for `site/data/explain.json`, which doesn't exist yet. The binding applies once the switch-on PR adds it.

## Protected path

`.github/workflows/explain.yml` gains one line, `MODEL: ${{ inputs.model }}`, in the summary step. Only the owner merges it (AGENTS.md "Merging").

## Still open (next)

Done since the first pin: refusal-parity wording (0009), and the consent window and network-address drafts (0010). Next: the contradictory $30 budget wording, which needs a check against current AWS Budgets documentation. Then the LOWs: the 28 s deadline, leaked reservations, the overrun disclosure and debts in headroom. The PR #12 LOW is optional.

## Reviews owed

- **Jarvis**, independently: 304 (0001, 0002, 0004), each fix 0003 and 0005–0008, and follow-ups 0009–0010. Claude does not self-clear; these tests are the author's own.
- Brad: the protected workflow line above, and all owner decisions (unchanged): adopt composed explanations; the evaluation set and the 80% floor; real names or stand-ins; the AWS sitting; protect-main; merges of #4, #6, #8, #10 and #12; the GitHub profile pin.

## Usage

The weekly meter was read directly in this desktop session: 48% when the thread started, **49%** at this checkpoint (unchanged at 14:02). Wednesday's stop is 55%.

## A slip, corrected

A cleanup command (`git checkout HEAD -- .`) discarded fix a's uncommitted edits. They were restored from git's own stash object (`e30d99e`), re-tested (17/17) and committed. No other effect.
