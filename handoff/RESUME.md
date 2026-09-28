# Resume guide (paused 2026-09-28, evening)

The owner paused for the week to save usage. Everything needed to pick up is on this branch. Nothing here is secret.

## Where things stand

- **The v2 preview is one pull request in biasclear/biasclear** (branch `claude/v2-preview`), built from `handoff/preview/preview-seed.bundle` (one parentless commit, tree `324f62314dbf9ed9516a8baed19734177fe1a24e`, rules 2.0.0a4). The owner merges it; merging publishes https://biasclear.github.io/biasclear/ as a Preview.
- **What was done to it:** E3 fairness rules through red-team round 5; rules hold no group names (lint-enforced); every real person and organization in test text replaced by a made-up name; the website and README; one five-lens red team (fairness, truth in copy, privacy and security, first impression and accessibility, code and CI) and one fix round for every finding. Tests at packaging: pytest 10,683 passed / 20 strict xfails; engine 137/137 three runs, parity identical; site and Playwright suites green.
- **Not done yet:** the fresh re-check of that fix round (it was stopped on purpose to save usage), and Jarvis's independent review.
- **Repository settings done (2026-09-28, owner's browser):** description, topics, Wiki and Projects off, auto-delete merged branches; read-only workflow token and all security scanners were already on. Still open: the `pypi` environment's approval rule (needed before the first release), require-2FA for the organization (owner's own tick), the Pages verified domain with its Namecheap TXT record, and review limits (fold into the mailbox run).

## Resume order (PM)

1. Check the pull request's CI and merge state; if merged, check the Pages deploy and the live site.
2. Fresh-eyes re-check of the merged tree (all five lenses); fix what it finds in follow-up pull requests. The fix round's open PM questions were accepted: plural objects ending a clause count for CAUSAL_TOTALIZATION; "Typical ___!" only before "!"; neutral stance words (activists, advocates, skeptics) are not labels; "pigs" is a known limit; CODEOWNERS lists paths without owners.
3. Jarvis: fill the constants in `handoff/jarvis/jarvis-review.sh` (branch, commit, PR number, brief URL and its sha256), move it to `ops/easy/`, add a queue item. The owner types "next" in the Hands thread and presses run. Read his answer from Drive (the shared Claude-Jarvis folder syncs there).
4. The `v1-final` tag (orphan commit from `handoff/v1-final-snapshot.tar.gz`), then a follow-up PR that links it.
5. Mailbox run (owner pays about $15): hello@biasclear.com, DMARC p=none, mail test; the Pages domain TXT and Verify; review limits; then PyPI with a passkey.
6. Render cleanup and the signup export; the public note, then the signup notice by about 2026-10-26.
7. Point biasclear.com at Pages; retire the old repository (this one). When retiring, remember that this branch's history and `handoff/biasclear-v2-work.bundle` hold older drafts, including real names in old test text and the old owner-steps draft.
8. Explain (Mode C, AWS): code in `handoff/explain/explain-c.patch` (apply on top of the preview tree; it was built on the tree just before the last fix round), design in `SPEC.md`, the owner's 14 decisions in `DECISIONS.md`. Still open from its red team: 1 high (the verdict screen can pass an answer that obeys an injected instruction) and 2 medium (side-word forms not caught symmetrically; the plainer rewrite can reverse the claim). Nothing is deployed and nothing costs money.

## Private items

The owner's private checklist and the signup-notice draft live in the owner's console and Google Drive ("BiasClear Archive"). The map from real to made-up test names was not kept: the v1 golden file in the repository stands on its own.
