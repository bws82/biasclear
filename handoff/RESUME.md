# Resume guide (paused 2026-09-27)

BiasClear v2 is paused while the owner finishes another project. This folder holds everything needed to pick it back up quickly. Nothing here is secret: the owner's private checklist lives in his private Owner Console, and private drafts live in his Google Drive "BiasClear Archive" folder.

## Before or during the pause (owner)

1. The 1-minute safety check at the top of the Owner Console: suspend the old v1 services if the old log still answers.
2. The one-time note to the old beta signups should go out by about **2026-10-26**. It needs the mailbox (console Sitting 4), the saved list, and the owner pressing Send. Start here if that date is close.

## What's in this folder

| File | What it is |
|---|---|
| `biasclear-v2-work.bundle` | Git bundle with three branches: `main` (the seed for the new repository), `e2-ts-engine` (browser engine, verified: 0 differences from Python in 6,258 scans), `e3-symmetry` (structural rules + fairness suite; the last commit is an interrupted round-3 fix, so re-run all tests before using it) |
| `v1-final-snapshot.tar.gz` | Scrubbed v1 code for the `v1-final` tag the preprint cites. Its one gitleaks hit is the known fake key literal in `tests/test_infra.py` (allowlisted in the seed's `.gitleaks.toml`) |
| `field-guide.md`, `field-guide.json` | Field Guide: 40 entries, every example re-checked against the engine. The two rules rebuilt in E3 still need entries |
| `homepage-lightbox.html` | Finished homepage design |

Restore the branches: `git clone handoff/biasclear-v2-work.bundle biasclear-v2 && cd biasclear-v2 && git branch -a`.

## Resume order (PM)

1. Read the Owner Console for anything the owner pressed during the pause (Done notes, especially the safety check).
2. Finish E3: restore `e3-symmetry`, run the full Python and TypeScript test suites and the parity script, and resume the red-team hunt from round 3 until a round comes back dry.
3. When the owner has done console Sittings 1 to 2: attach `biasclear/biasclear`, build the seed commit on top of its README commit, push the `claude/` branch, open the seed PR, and unlock Sitting 3.
4. Hosting decision (dream session 2026-09-27): the site and both AI modes on AWS (S3 + CloudFront free plan; Mode C = Lambda + Bedrock with an IAM role, spend cap $25/month default, budget alert with credits excluded, one-file CloudFormation setup, GitHub OIDC deploys, no stored keys). GitHub Pages is the fallback. Render stays idle. The AWS Activate credit is $978.57, valid until 2028-03-31, and has been covering Claude on Bedrock. Build the CloudFormation template and have it red-teamed before the owner runs it.
5. Update `ops/BLUEPRINT.md` and `ops/BOARD.md` for the AWS hosting decision (the owner merges).

## Where everything else is

- Plan: `ops/BLUEPRINT.md` (revision 3) and `ops/BOARD.md` on this branch.
- Agent rules: `AGENTS.md`.
- Owner steps: the private Owner Console (claude.ai artifact; the owner has the link).
- Private: the PIT v2 corrections memo (sent to the owner), the signup-notice draft (Drive), and the old-project inventory (Drive sweep, 2026-09-27).
