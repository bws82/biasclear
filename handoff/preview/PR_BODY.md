BiasClear v2, the whole public preview in one pull request. There is no ticket for it: this is the seed that the rest of the work builds on.

## What changed

**For the owner, in plain words:** merging this puts the new BiasClear on the main page of this repository and publishes the website at https://biasclear.github.io/biasclear/, labelled **Preview**. The checker runs inside the visitor's browser and sends nothing anywhere. It marks the persuasion moves in a text and names each one. It points at wording, never at people or sides, it is not a fact-checker, and it publishes no accuracy figure until one is measured on data someone else labelled.

What is in it:
- **The rule pack** (`rules/biasclear-rules.json`, 43 rules, rules version 2.0.0a4). No rule names, or holds a word built from, a person, party, ideology, faith, country, program, outlet, institution or school. A lint enforces this (`tests/test_neutrality_lint.py`). The one exception is the sentence-splitting abbreviation list, and it is documented.
- **Two engines** from that one pack: Python (`src/biasclear`, zero runtime dependencies) and TypeScript (`packages/engine`, zero dependencies), checked against each other by parity tests.
- **A fairness suite** (`tests/test_symmetry.py`) that swaps one side's names for the other's in the same sentences. Every name in test text is made up.
- **The website** (`site/`): the checker, the Field Guide to every move, and the Method, Privacy and About pages. It is deployed by `.github/workflows/pages.yml` from `main` only.
- **The README, CHANGELOG, `rules/RULE_CHANGES.md`** (every change from v1 and why), SECURITY.md, AGENTS.md and the public plan in `ops/`.

## How I know it works

Run on this exact tree before packaging:
- `python -m pytest -q`: 10,683 passed, 20 expected failures (strict: the known limits below).
- `cd packages/engine && npm ci && npm test`, three runs: 137 of 137 each time, parity identical each time.
- `node scripts/build-site.mjs`, then `node --test site/test/site.test.mjs` (27 passed) and the Playwright suite `site/test/browser.test.mjs` (16 passed; phone and desktop sizes, both themes, no requests after load).
- The wheel and sdist build; the sdist's own test run passes; the wheel installs in a clean environment and the command-line tool works.
- A personal-data and secrets scan over every file: the only personal name is the paper citation.
- Five red-team reviews (fairness, truth in copy, privacy and security, first impression and accessibility, code and CI), then one fix round for everything they found.

## Numbers that changed

All from `python scripts/site_facts.py`:
- 8,313 swapped template pairs from 135 name and label pairs, in 12 groups.
- 1,480 red-team pairs.
- 20 known limits, each with a written reason, run as strict expected failures.
- 48 retired pairs (pairs that swap the kind of word, not the side), listed with reasons in `rules/RULE_CHANGES.md`.

## Protected paths touched

All of them, because this is the seed: `AGENTS.md`, `CLAUDE.md`, `LICENSE`, `README.md`, `.github/` and `ops/BLUEPRINT.md`. **The owner merges.**

## Found along the way

- The last fix round was not re-checked by a fresh red team yet. That re-check, and an independent review by a second model (Jarvis), come next and land as normal follow-up pull requests.
- The retired v1 code will be kept at a `v1-final` tag after this merges. The README describes it in the future tense and links nothing yet.
- `.github/requirements-release.txt` pins the release build tools with hashes. The release workflow needs the `pypi` environment's approval rule before the first release; that is set up at release time.

## Questions for the PM

None.

## Airtight self-check
- [x] No secrets, tokens or credentials anywhere in the diff, tests, logs or this text
- [x] No personal information about any person; commits use a noreply identity
- [x] No network calls from the engine; no cookies, analytics, third-party scripts or trackers on the site
- [x] Safe rendering: untrusted text reaches the page only as text (no innerHTML or similar sinks, no href or src from text)
- [x] Rules match structure only (no named people, parties, outlets or institutions); swapped-pair tests added
- [x] Every public number traces to a script in this repo
- [x] Accessible: keyboard path, tier not shown by color alone, contrast checked, reduced motion respected
- [x] Protected paths are changed on purpose (this is the seed); no Codex handle in this text

— Claude (PM)
