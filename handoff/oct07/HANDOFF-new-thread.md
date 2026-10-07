# BiasClear handoff for a new thread (Wed Oct 7, Claude)

Paste or point the new thread at this file:
bws82/biasclear, branch `claude/biasclear-revival-strategy-xvdgjm`, `handoff/oct07/HANDOFF-new-thread.md`.

## Roles and rules
- **Brad** (GitHub bws82) owns BiasClear and makes every final call.
- **Claude** is BiasClear coordinator and sole writer through Sun Oct 11. **Jarvis (GPT/Codex)** is reserved for Soldiers' Angels. Jarvis independently reviews Claude's changes; Claude never self-clears.
- Read `AGENTS.md` in biasclear/biasclear first. The live plan is `ops/BOARD.md`.
- None of the following:
  - AWS changes or calls, or paid model calls;
  - merge, deploy or a model switch;
  - settings, access or public-site changes;
  - capacity purchases;
  - a Codex wake (CLI, child task or automation);
  - broad fan-out workflows, watchers or scheduled resumes.
- New AWS/Bedrock spend is $0; the $25 later-live cap stays.
- Nothing goes public without Brad's yes. No keys or secrets anywhere. Never delete in Drive.
- Protected paths are merged by the owner only: AGENTS.md, CLAUDE.md, LICENSE, README.md, .github/, ops/BLUEPRINT.md, ops/OWNER_STEPS.md.
- Commits use the author `BiasClear <noreply@biasclear.com>`.
- Soldiers' Angels: M365 is view-only for every AI; never change Salesforce records. Gmail and Calendar: no send without Brad's approval of that exact message.
- Model Check: the 28 draft questions are unapproved and must not be run, not even against a stub.

## Approved plan, Oct 7–11
Full text in `handoff/oct07/plan-oct07-11.md`.

**Usage ceilings** (from a 47% baseline):

| Day | Ceiling |
|---|---|
| Wed | +8 (stop by 55%) |
| Thu | +12 |
| Fri | +12 |
| Sat before refill | +6 (confirm the refill at 7 p.m.) |
| Sat after refill | +5 |
| Sun | +10 |

- Hard stop at 85%.
- A cloud session can't read the meter. At each checkpoint, ask Brad for his app's weekly %; consumed usage stays "unverified" until he answers.

**Days:**
- **Thu:** fix the injection, spending-control and privacy findings, with regressions.
- **Fri:** integrate the checker and backend, fixtures, tests and the offline stub evaluation.
- **Sat:** remaining fixes, privacy draft, decisions and the review packet.
- **Sun:** freeze. The Model Check harness only if Explain is stable; its questions stay unrun.

## Repos and state
- **biasclear/biasclear** (public, new v2). Read-only from the cloud session, via `git fetch origin refs/pull/N/head`.
  - main `2b39303`
  - PR #4 (domain links) `ae5a432`
  - PR #6 (board)
  - PR #8 (UI) `bee6d58`
  - **PR #10 Explain**: original head `2299fe1`, now `19eebb3`, 8/8 checks green
  - PR #12 (test-only) `adccb37`
  - dependency PR #3 `95e179f`
- **bws82/biasclear** (the old v1 repo). The save branch `claude/biasclear-revival-strategy-xvdgjm` is at `2ca891f`, with draft PR #21. Every Claude checkpoint is a pinned patch here.

**Wednesday work, all done (`handoff/oct07/`):**

| Item | Where | State |
|---|---|---|
| 304, composed explanations | `composed-304/` | Base 2299fe1 → commit `47952e1`, patch sha256 `e75a9f54…a0827d`. Prototype; **Brad decides adoption**; Jarvis's review is owed. |
| 306, backend review of PR #10 @ 19eebb3 | `backend-306/REPORT-306.md` | NO-GO until the five ★ MEDIUM items are fixed |
| 311, PR #12 review | `pr12-review-311.md` | GO, one LOW |
| Checkpoint and ranked findings | `checkpoint-wed.md` | — |

How 304 works:
- The model picks reviewed phrase ids. The server writes `The words “<exact mark>” … The sentence does not say …`.
- The mark is quoted exactly or the reply is refused.
- The limits count the whole text; per-mark pick limits keep every allowed choice within them.

**Drive** (shared folder `1u2UYgsMl7bs7Uf9uPbF4gdaDMDknuom3`, files named `NNN-from-to-topic.md`):
- Latest from Claude: 304, 306, 311, 312.
- Latest from Jarvis: 309.
- Next free number: 313.

## Next: Thursday
Offline integration candidate on PR #10's exact head `19eebb3`. Pin it on the save branch; do not publish to PR #10.

1. Apply the 304 patch plus `composed-304/integration-note.patch`:
   - the rule id at app.ts:285, dry-run.ts:64 and handler.test.ts:375/474;
   - the helpers;
   - move 13 handler/nolog/dry-run expectations to slot JSON;
   - pre-check `quotable`/`pickLimits` before the model call.
2. Fix with regressions, in order:
   - (a) preflight-rejected rows must make the evaluation incomplete;
   - (b) pause and debt must not share a transaction with the contended item;
   - (c) a definite settle cancellation must not cause a permanent pause or discard the answer;
   - (d) the billing-anomaly metric filter must match Lambda's log format;
   - (e) a model change on deploy must be named in the consent and the approval summary.
   Then the refusal-parity wording, the consent vs. 15-minute window, and the privacy drafts on network addresses.
3. Checkpoint: SHA, files, tests, open findings, reviews owed, usage (ask Brad for his %).

## Open decisions (Brad)
- Adopt composed explanations?
- Evaluation set and the 80% floor.
- Real names vs. stand-ins.
- AWS sitting.
- Protect-main.
- Merging PRs #4, #6, #8, #10, #12.
- The public face:
  - Brad's GitHub profile pins **bws82/biasclear** (v1, AGPL, "Structural bias detection and correction engine built on PIT"), not the new biasclear/biasclear;
  - point it, or pin the new repo, with his yes.
- biasclear.com:
  - not yet checked live (see below);
  - the last DNS lookup showed 216.24.57.1, which is Render (possibly the old v1 host).

## Note on the cloud thread
The old cloud thread's network proxy refused biasclear.com, www.biasclear.com and biasclear.github.io every time from Sept 26 on. GitHub, Drive and npm worked. First thing in the new thread: try to open biasclear.com and report what a visitor sees.
