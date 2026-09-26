# BiasClear v2 board

Maintained by the PM (Claude). Last updated: 2026-09-26.

**Goal:** a free, browser-only persuasion checker whose numbers are measured and whose neutrality is tested on every release. It should feel remarkable the first time someone pastes text into it.

**Launch window:** week of November 16, 2026 (after the November 3 election).
**Renewal decision:** February 1, 2027 (the domain renews February 18, 2027).

## Gates

| Gate | Passes when | Who approves |
|---|---|---|
| **A: launch-ready** | Symmetry suite green; benchmark numbers published by a script; site passes the airtight checklist; zero secrets in the tree | Owner |
| **B: keep going** (Feb 1) | About 1,000 checker visits; at least one outside signal (educator, citation, researcher or journalist, or 50 stars); owner's time stayed within budget | Owner |

## Tracks

### 0: Cleanup and claims (PM, now)
- [x] Withdraw v1 accuracy, neutrality and compliance claims (README, v1 docs marked archived)
- [x] LLM-proposed rules no longer auto-activate; human `approve()` required
- [x] Fix the README quick start (async) and the citation
- [x] Agent charter (`AGENTS.md`), PR template, this board
- [ ] Owner click-paths: Render cleanup, Namecheap two-factor, GitHub org (see `ops/OWNER_STEPS.md`)
- [ ] Owner: branch protection on `main` (PR required, all four checks required, no force-push) before any agent merge
- [ ] Relicense proposal (Apache-2.0 engine, CC BY 4.0 rule pack) as its own PR for the owner

### 1: Engine v2 (Codex builds, PM reviews)
- [ ] **E1** Extract all rules into one versioned rule pack (`rules/biasclear-rules.json`); the Python engine loads it; output unchanged on all existing tests
- [ ] **E2** Zero-dependency TypeScript engine (`packages/engine`) that reads the same rule pack, including citation suppression; golden-file parity with Python
- [ ] **E3** Symmetry: replace named-entity lists with structural rules; 100+ swapped-pair cases; CI gate
- [ ] **E4** Benchmark harness on public, externally labeled sets (SemEval-2020 Task 11, SemEval-2023 Task 3 English): download script only, never redistribute data; per-rule precision and recall written to `bench/results/*.json`
- [ ] **E5** Retire the v1 "truth score": replace it with per-move highlights plus a transparent move count; no single score of truth

### 2: Our own labeled set (PM designs, no paid labelers)
- [ ] **L1** Written labeling guide (what counts as each move, what doesn't)
- [ ] **L2** Separation of duties: the rules are frozen and hashed *before* labeling. Labels come from a separate agent session that never sees the rules. The owner spot-checks a random 10%. Labels, guide and hash are all published so anyone can challenge them.

### 3: Brand and site (PM designs, Codex builds)
- [ ] **B1** Owner picks a brand direction from the live prototypes
- [ ] **B2** Design tokens and wordmark (SVG), tier colors, type (self-hosted)
- [ ] **S1** Static site (Home checker, Field Guide, Method, Developers, About) on Cloudflare Pages through Git integration (no deploy tokens in the repo)
- [ ] **S2** Share cards rendered locally (no server), poster PDF of the Field Guide

### 4: Distribution (after Gate A)
- [ ] **D1** npm and PyPI under a BiasClear-owned account with Trusted Publishing
- [ ] **D2** MCP server so AI agents can lint their own drafts
- [ ] **D3** Browser extension (after Feb 1, if users show up)

### 5: Lab
- [ ] **F1** Fidelity Trace: compare a source against a retelling and show what was dropped, hardened, unsourced, or had its numbers changed

## Decisions log

| Date | Decision | By |
|---|---|---|
| 2026-09-26 | Relaunch: honest, browser-only, launch week of Nov 16, build starts now | Owner |
| 2026-09-26 | Agents may push branches and open PRs | Owner |
| 2026-09-26 | Labeling is done in-house (no paid labelers) | Owner |
| 2026-09-26 | Owner is not featured on the site; small citation plus a contact address only | Owner |
