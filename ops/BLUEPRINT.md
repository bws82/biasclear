# BiasClear v2 blueprint

Owner: the project owner. Author: the PM (Claude). Status: **proposed**, pending owner approval. Date: 2026-09-26.

This page settles every account, key, model, agent and hosting choice before anything more gets built. Anything not written here isn't decided. Changing a decision means changing this page first.

---

## 1. Principles

1. **Measure before cutting.** No build ticket starts until this page and the ticket agree.
2. **Nothing to steal.** The public product holds no user data, no secrets and no server state. What doesn't exist can't leak.
3. **No stored credentials where a keyless option exists.** Build and publish jobs use short-lived identity tokens (OIDC). A stored key is allowed only where no keyless path exists, and then it's scoped, spend-capped, and lives in one place.
4. **Every public claim is produced by a script.** Numbers come from code in the repo, never from memory or marketing.
5. **The owner holds the keys; agents hold the tools.** Account creation, passwords, two-factor, payment methods and first-time key creation stay with the owner. Agents do everything after that.
6. **Three sets of eyes on every change:** the builder writes it, the red team attacks it, the PM decides. The owner approves at gates.

---

## 2. Who does what

| Role | Who | Does | Never does |
|---|---|---|---|
| Owner | The project owner | Vision, gate approvals, account security, payment methods | Routine code review |
| PM | Claude | Plan, tickets, design, code review, merges (once `main` is protected) | Hold passwords, create accounts, spend money |
| Builder | Codex | Implements tickets as PRs | Merge, touch accounts, change `AGENTS.md` |
| Red team | Jarvis (GPT) | Attacks every PR and every public claim before merge. Hunts asymmetric pairs, leaks, overclaims and security holes | Write product code, merge |
| Memory | The owner's Super Brain vault | Long-term project history the PM reads before big decisions | — |

**Signatures.** All three agents post through the owner's GitHub account, so every agent comment or review must end with its role line: `— Codex (builder)`, `— Jarvis (red team)` or `— Claude (PM)`. An unsigned agent post is treated as unverified.

**Red-team loop.** When Codex marks a PR ready, Jarvis reviews it and posts one review that starts with `RED TEAM:`. It lists findings as **blocking** or **note**. Every red-team pair that exposes asymmetry becomes a permanent test case. The PM merges only when every blocking finding is fixed or answered in writing.

---

## 3. Accounts map (the single list)

| Asset | Where | Owner action | Status |
|---|---|---|---|
| Domain `biasclear.com` | Namecheap | Two-factor on (step 1) | Paid to Feb 18, 2027 |
| Public contact `hello@biasclear.com` | Namecheap email forwarding | Add alias (step 6) | To do |
| Code | GitHub `bws82/biasclear`, moving to a `biasclear` organization | Create org (step 7, option A) | Decision pending |
| Website hosting | **Render**, as a free Static Site on the existing account | Keep account, delete v1 service (step 2) | Recommended below |
| Python package | **New PyPI account** under the project, publishing by Trusted Publishing | Create account + two-factor (new step) | To do |
| npm package | New npm account/org `@biasclear`, Trusted Publishing | Create account + two-factor (later, before D1) | Later |
| AI (internal jobs) | AWS Bedrock if the ~$1,000 credit is live, otherwise the Anthropic API | Check credits (step 3) | Waiting on owner |
| AI (hosted second opinion) | Anthropic API, own workspace with a hard monthly spend limit | Create console org + limit (later, after Gate A) | Later |

**Why Render for the site.** The owner is keeping the Render account anyway. Static Sites there are free, and the ~$500 credit stays in reserve for the one server we might add later (section 4, mode C). That's one fewer vendor. DNS stays at Namecheap. If the owner prefers Cloudflare Pages, the site is plain static files, so switching takes an hour.

---

## 4. The AI layer

**Model: Claude Opus 5.5 (`claude-opus-5-5`)**, per the owner's pick. It costs $4 per million input tokens and $20 per million output. A typical second-opinion check (about 1,500 tokens in, 600 out) costs roughly **1.8 cents**.

Three things to know about this model:
- It always thinks. You control depth with `effort`, which defaults to `medium`, so set it explicitly.
- Forced tool calls aren't allowed. Use structured outputs for JSON results.
- It's newly launched, so confirm Bedrock carries it (Bedrock console, **Model access**) before we plan on the credit.

**Three modes, launched in order:**

| Mode | What | Who pays | Keys | When |
|---|---|---|---|---|
| **A. Rules only** | The deterministic checker, in the browser | Nobody | None | Launch |
| **B. Bring your own key** | Visitor pastes their own Anthropic key; the browser calls Anthropic directly; the key stays in their browser | The visitor | Visitor's own | Launch (optional switch) |
| **C. Hosted second opinion** | A tiny Render service calls Opus 5.5 for visitors without a key: per-visitor daily cap, input-length cap, stores nothing, logs no text | Project (credit first) | One project key in Render's secret store, workspace spend limit $50/mo | Only after Gate A, only if people ask for it |

**Internal AI jobs** (the blind labeler, benchmark runs, red-team sweeps) run from GitHub Actions:
- **If the AWS credit is live:** Bedrock through GitHub OIDC into an IAM role that can call Bedrock and nothing else. **No stored AWS keys anywhere.**
- **Otherwise:** the Anthropic API through Workload Identity Federation from GitHub Actions, which is also keyless. Fallback is one key stored as a GitHub Actions secret, in its own spend-limited workspace.

**Turnkey for the owner.** Each account step is a click-path of 10 minutes or less in `ops/OWNER_STEPS.md`. The owner never copies a key into chat, a document or a file. Where a key must exist, the owner pastes it straight from the provider's page into Render's or GitHub's secret field, following the exact field names the PM gives.

---

## 5. Security model

| Threat | Control |
|---|---|
| A secret committed to the repo | Secret scan on every PR; the `AGENTS.md` hard rule; keyless publishing and CI |
| A stolen key running up a bill | Keyless where possible; spend limits per workspace; AWS $5 budget tripwire |
| User text leaking | Rules run in the browser; mode C stores and logs nothing; no cookies or trackers |
| An agent loosening its own rules | `CODEOWNERS` requires owner review on `AGENTS.md`, `ops/`, `.github/`, `LICENSE`, `README.md`; `main` is protected |
| A package name squatted | Reserve `biasclear` on PyPI as a pending Trusted Publisher before first release |
| Personal information exposed | No bio on the site; noreply commits; contact via `hello@` only; clean-history repo (option A) |
| Rules that tilt politically | Structural-only rules; 120+ swapped pairs as a CI gate; red team adds new pairs every review |
| Account takeover | Two-factor (authenticator app) on Namecheap, GitHub, Render, PyPI, npm, AWS and the Anthropic console |

---

## 6. The years of prior work (the desktop folder)

The owner's desktop folder is the project's history, with the Sophos system already stripped out and replaced by the Super Brain. Intake plan:

1. The owner zips the folder and puts it in a private Google Drive folder named `BiasClear Archive`. It never goes into GitHub.
2. The PM reads it, lists what's there, and flags anything that looks like a secret for the owner to rotate. Nothing gets copied into the repo without a ticket.
3. Worth salvaging goes into tickets: early pattern ideas, labeled examples, PIT drafts, design assets.

---

## 7. Build order

| Phase | Work | Gate |
|---|---|---|
| 0 | This blueprint approved; owner steps 1–6 done; merge rights live | Owner says "approved" |
| 1 | E1 rule pack, E2 browser engine, E3 symmetry | Red team finds no asymmetric pair it can't turn into a passing test |
| 2 | Brand pick, design system, site on Render (mode A + B) | Owner reviews the staging URL |
| 3 | E4 benchmark + blind-labeled set; PIT v2 preprint | Numbers published by script |
| **Gate A** | Launch, week of November 16 | Owner |
| 4 | PyPI and npm through Trusted Publishing; MCP server; mode C if wanted | Owner |
| **Gate B** | February 1, 2027: keep going or shelve | Owner |

---

## 8. Open decisions (owner)

1. Approve this blueprint as written, or mark changes.
2. Brand direction: A, B, C or a mix.
3. Repo home: option A (new `biasclear` org, clean history) is the PM's pick.
4. License: Apache-2.0 for the engine plus CC BY 4.0 for the rule pack, as its own PR.
5. Signup notice: send the short note to pre-March-20 signups, yes or no.
