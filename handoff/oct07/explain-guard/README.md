# Explain checker packet (Claude's share of the fixes for PR #10)

The split is agreed in Drive files 299 and 300. This packet is a patch for Jarvis to integrate. It is not pushed to biasclear/biasclear.

## The patch

- File: `explain-guard.patch`, one commit, `git am`-ready.
- Based on reviewed head `2299fe1a527d4c291248ed310574f384ffe0f70b`.
- Commit e39e44b, author BiasClear <noreply@biasclear.com>.
- sha256: see 301 or run `sha256sum explain-guard.patch`.

Files:
- `packages/explain/src/howguard.ts` (new)
- `packages/explain/src/output.ts`
- `packages/explain/src/prompt.ts`
- `packages/explain/test/howguard.test.ts` (new)
- `packages/explain/test/output.test.ts`
- `packages/explain/test/prompt.test.ts`
- `packages/explain/test/fixtures/redteam-bypasses.json` (new)
- `packages/explain/test/fixtures/honest-calibration.json` (new)

## Checks run on the patched tree

| Check | Result |
|---|---|
| `npm test` in packages/explain (typecheck, build and its network scan, vitest) | 634 passed |
| `npm run eval:dry` | the same tables as at the reviewed head; 0 network attempts |
| Root `pytest tests/test_neutrality_lint.py tests/test_readme.py` | 26 passed |
| Red-team probes (`probes/`) | 0 of the 173 earlier bypasses pass; only the honest baseline passes |

## Honest-answer acceptance

The calibration files are in `calibration/`.

| Set | Reviewed head | This patch |
|---|---|---|
| A, 172 answers in two styles (used to tune the word list) | 37 | 80 |
| B, 86 answers in a third style (held out) | 17 | 35 |

These are written answers, not real model output. The real measure is the owner-approved run.

## Proposed fixtures (M10/L8)

These are in `fixtures-proposed/`. Nothing in them has been merged, and they need Brad's approval before any run:
- 48 mirrored pairs and 24 side-free controls;
- 16 moves and 11 topics;
- stand-in names in place of real party names;
- each side goes first 24 times.

Every sentence was checked with the real engine (rules 2.0.0a5).
