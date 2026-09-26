# AGENTS.md: how work gets done on BiasClear

Every agent reads this first: Codex, Claude, and any other agent. It sits above any other doc in this repo. If a ticket conflicts with it, stop and ask (see "Talking to the PM").

## Roles

| Role | Who | Owns |
|---|---|---|
| Owner | The project owner (human) | Vision, final calls, gate approvals. Never the bottleneck for routine work. |
| PM / lead reviewer | Claude | The board (`ops/BOARD.md`), tickets, design direction, code review, merges into the integration branch |
| Builder | Codex | Implementing tickets as pull requests |

Agents never ask the owner directly. Questions go to the PM, who batches anything that truly needs the owner.

## The loop

1. **Tickets are GitHub Issues** labeled `agent:codex`. Take the lowest-numbered open one whose `Depends on:` tickets are merged.
2. **Claim it by opening a draft PR within your first commit.** Name the branch `codex/<issue-number>-<short-slug>` and put `Closes #<issue>` in the PR body. A draft PR is how the PM knows you're on it.
3. **Base branch:** `main`, unless the ticket names another.
4. **One ticket per PR.** Keep diffs focused and don't fix unrelated things; note them in the PR under "Found along the way".
5. **Mark the PR ready for review** once the Definition of Done below holds. The PM reviews, then merges or requests changes.
6. **Talking to the PM:** comment on your own PR with a line that starts `@pm`. The PM is subscribed to PR activity, while issue comments may go unseen. For a blocking question, post it and keep working on whatever isn't blocked.

## Definition of done

- `python -m pytest tests/ -q` passes. For any TypeScript package, its own `test` script passes.
- New behavior has tests. Every rule change comes with positive examples, negative examples, and **swapped-pair symmetry cases**.
- No new runtime dependency without a one-line justification in the PR. The browser engine has **zero** runtime dependencies.
- The PR body fills in every section of `.github/pull_request_template.md`.
- The self-check at the bottom of the template is ticked honestly.

## Airtight rules (hard stops, no exceptions)

A PR that breaks any of these gets closed, not fixed in review.

**Secrets**
- No keys, tokens, passwords or credentials anywhere: code, tests, fixtures, scripts, docs, commit messages, PR text or logs. Not even "example" values that look real.
- Package publishing (npm, PyPI) uses **GitHub OIDC Trusted Publishing only**. Never create or store a publish token.
- No new external service, account, webhook or third-party API without PM approval in the ticket.

**Privacy of people**
- Don't add personal information about anyone to the repo or the site: no personal names beyond the paper citation `Slimp, 2026`, no personal email addresses, phone numbers, locations, employers, or legal matters.
- Commit as a `noreply` identity. Never commit with a personal email address.
- The public contact is `hello@biasclear.com`, nothing else.

**Privacy of users**
- The engine makes **no network calls**. The site sets **no cookies** and loads **no third-party scripts, fonts or trackers** (self-host everything). Cloudflare's cookieless Web Analytics is the one pre-approved exception, and only the PM wires it.
- User text never leaves the browser. The only exception is the optional "second opinion" mode, which calls the **user's own** AI provider with the user's own key, stored only in their browser, and is labeled at the switch.

**Truth in copy**
- Every number shown publicly must be produced by a script in this repo, and the copy must cite that script.
- Never use these words or ideas: "truth score", "accuracy" without a named benchmark, "certified", "compliant", "detects lies", "AI-powered" for deterministic scans.
- Say what we miss next to what we catch.

**Neutrality**
- Rules match **structure**, never named people, parties, outlets, institutions, schools or ideologies. Any rule that contains a proper-noun list is rejected.
- Every rule ships with swapped-pair tests (left/right, institution/institution, credential/credential), and the symmetry suite is a CI gate.

**History**
- Never force-push to `main` or rewrite shared history. Never commit generated secrets, `.env` files or local databases (`*.db`).

## Repo map (v1, being rebuilt)

- `biasclear/frozen_core.py`: the 42 deterministic rules and scoring inputs. This is the source that v2's rule pack is extracted from.
- `biasclear/detector.py`, `biasclear/scorer.py`: scan pipeline and scoring.
- `biasclear/patterns/learned.py`: the LLM-proposed rule "learning ring". Activation requires human `approve()`; don't add auto-activation.
- `api/`: the v1 FastAPI server. **Retired.** Don't extend it. v2 is static and browser-only.
- `calibration/`: v1 self-graded corpus. Not a benchmark. Don't quote its numbers.
- `ops/BOARD.md`: current plan, gates and ticket status (maintained by the PM).

## Voice (for any user-facing words)

Plain, calm and exact. Short sentences. Show, don't assert. No hype, no fear, no "revolutionary". We point at structure, never at people.
