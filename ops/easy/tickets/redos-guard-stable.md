## Problem

`packages/engine/test/redos.test.ts` fails when any pack regex takes 50 ms or more (best of three runs) on a 20,000-character adversarial string. On GitHub's shared runners that wall-clock limit is noisy:

- On PR #1 the required `test` job failed once with `VAGUE_INSTITUTIONAL_APPEAL[0]` at 52.5 ms, and passed on re-run with no change.
- Earlier, `MEDIA_WEASEL_QUANTIFIERS[0]` measured 46 to 59 ms depending only on which tests ran before it (commit 5705e8f moved the guard first to work around it).

A required check that fails at random teaches people to press re-run, which defeats the guard.

## Goal

The guard fails for super-linear regex behaviour (polynomial or exponential backtracking), and never because a runner is busy. It must not get weaker at what it protects against.

## Suggested approach (not binding; explain whatever you choose)

- **Judge growth, not one time.** Time each regex on the same adversarial unit at two or three lengths (for example 5,000, 10,000 and 20,000 characters, best of several runs each), and fail when the time grows clearly faster than the length. Ignore timings below a small floor, where noise dominates.
- **Keep an absolute ceiling as a backstop,** set high enough that a linear pattern never reaches it on a slow runner (for example 500 ms at 20,000 characters), so a catastrophic pattern still fails at once.
- **Cut noise at the source:** compile and warm each regex before timing it; re-time only the candidates near a threshold; run the guard in its own test file without parallel workers.
- Apply the same method to the Python timing tests in `tests/test_engine.py` if they share the problem.

## Acceptance

1. **Mutation proof.** In a scratch copy of the pack, re-introduce each regex the guard has caught before, and show the new guard fails on every one: the author-year citation token that held the en and em dash (rules 2.0.0a3); the quadratic `CREDENTIAL_AS_PREMISE` alternatives (2.0.0a3); the `INSTITUTIONAL_POSITION_AS_SETTLED` and `MEDIA_EMOTIONAL_LEAD` sentence-start loops (2.0.0a4); the whitespace rescans (2.0.0a5). Put the commands and their output in the PR.
2. **Nothing removed.** No rule, adversarial shape or input string is dropped, and the number of strings tested does not go down.
3. **Stable.** `npm test` in `packages/engine` passes 30 runs in a row while a second `npm test` runs alongside it; the PR's `test` check passes on three re-runs.
4. **Not slower to matter.** The guard still finishes inside its 120 s timeout, and its total time grows by no more than half.
5. **Explained.** The test's header comment says how the method works, in plain words. No public copy and no rule changes.

Out of scope: any change to `rules/biasclear-rules.json` or to what the rules match.
