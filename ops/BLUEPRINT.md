# BiasClear v2 blueprint

Owner: the project owner. Author: the PM (Claude). Status: **proposed (revision 2)**, pending owner approval. Date: 2026-09-27.

Revision 2 incorporates a red-team pass: six independent reviewers, with every finding checked by three skeptics. 72 of 73 findings held up. The owner's click-list lives in [`ops/OWNER_STEPS.md`](OWNER_STEPS.md). This page is the reasoning behind it.

Nothing is decided unless it's written here. Changing a decision means changing this page first.

---

## 1. Principles

1. **Measure before cutting.** No build ticket starts until this page and the ticket agree.
2. **Nothing stored that could be stolen.** The launch product runs in the visitor's browser: no server, no database, no user data, no secrets. (This is a design goal with named exceptions in §4, not a slogan.)
3. **No stored credentials where a keyless option exists.** Publishing and CI use short-lived GitHub identity tokens (OIDC), scoped to one repo, one workflow and one protected environment.
4. **Every public number is produced by a script in the repo.** If the script isn't there, the number isn't published.
5. **The owner holds the keys; agents hold the tools.** Accounts, passwords, two-factor, payment methods and deletions are the owner's clicks. Owner steps are **web clicks and decisions only**: no terminal, no code, at most 30 minutes per sitting, at most 2 hours a week.
6. **Accessible to everyone.** WCAG 2.2 AA is a launch requirement, not polish.

---

## 2. Who does what

| Role | Who | Does | Never does |
|---|---|---|---|
| Owner | The project owner | Vision, gate approvals, account security, payment, deletions, merges on protected paths | Terminal work, code review |
| PM | Claude | Plan, tickets, design, code review, merges on unprotected paths, starts Codex tasks | Create accounts, spend money, bypass rulesets, merge protected paths |
| Builder | Codex | Implements tickets as PRs | Merge, touch accounts, edit `AGENTS.md` or rulesets |
| Red team | An independent Claude review session run by the PM on every PR, plus Jarvis (GPT) as a second opinion at gates | Attack changes and public claims | Write product code, merge |
| Memory | The owner's Super Brain vault | Project history the PM reads before big decisions | — |

**One GitHub identity.** Claude, Codex and the owner all act through the owner's GitHub account, so GitHub can't tell them apart. That means:
- **Code-owner review can't be enforced by GitHub.** The author and the code owner are the same account, and GitHub won't let an account approve its own PR. The ruleset on `main` therefore requires status checks, not approvals.
- **Protection comes from process plus required checks.** The PM never merges a PR that touches a protected path (`AGENTS.md`, `CLAUDE.md`, `LICENSE`, `README.md`, `.github/`, `ops/BLUEPRINT.md`, `ops/OWNER_STEPS.md`). For those, the PM posts a plain-language summary page, and the owner clicks Merge.
- **Signatures label, they don't authenticate.** Every agent post ends with a role line (`— Codex (builder)`, `— Red team`, `— Jarvis (red team)`, `— Claude (PM)`). Anyone can type a role line on a public repo, so only posts from the owner's account count.
- **Later, optional:** a separate machine account for agents would let GitHub enforce owner review. It costs the owner a second account and reconnecting both agents, so it waits until the workflow proves itself.

**How Codex gets work.** Codex cloud doesn't poll for tickets. The PM opens a stub draft PR for the ticket and comments `@codex implement #N per AGENTS.md`. If that trigger fails, the fallback is the owner pasting one fixed line into Codex. Codex needs its GitHub connector installed on the new organization first (owner step).

**How the red team works.** The ChatGPT GitHub connector is read-only, so Jarvis probably can't post reviews. The standing red team is therefore an independent Claude review session (a separate multi-agent pass like the one that produced this revision). It posts one `RED TEAM:` review per ready PR with each finding marked **blocking** or **note**, and sets a `redteam` label (`redteam:clear` or `redteam:blocking`). Jarvis reviews at gates: the PM prepares a link, the owner shares it with Jarvis, and Jarvis's answer is posted verbatim, labeled as his. Every asymmetric pair any reviewer finds becomes a permanent test case.

---

## 3. Accounts map

| Asset | Where | Status / next |
|---|---|---|
| Domain `biasclear.com` | Namecheap | Paid to Feb 18, 2027. Two-factor on. **Auto-renew on** while any project account recovers through the domain. |
| DNS | Namecheap | Today it still points at Render. **The DNS records are removed in the same sitting the Render services are deleted**, or someone else could claim the domain on Render. |
| Project mailbox `hello@biasclear.com` | Namecheap Private Email, Launch plan (one mailbox; same account as the domain) | Replaces forwarding, so replies go out as hello@ instead of from a personal inbox. SPF, DKIM and DMARC records set when it's created. Recovery address for every project account. |
| Code | New GitHub organization `biasclear`, repo `biasclear/biasclear` | Seeded from a **scrubbed snapshot** (no old history, no personal data). The old `bws82/biasclear` becomes a one-file stub pointing to it, because the published preprint links there. |
| `bws82/biasclear-action` | Old GitHub Action | **Delete first.** It runs `pip install biasclear` while that name is unclaimed. Nothing depends on it (GitHub code search: 0 users). |
| Website | **GitHub Pages** on `biasclear/biasclear` | Free, no bandwidth tier to watch, no extra vendor, no deploy secrets. (Render's free tier now caps outbound bandwidth at 5 GB a month.) |
| Render | Existing account, about $500 credit | Both v1 services (`biasclear` and `biasclear-api`) deleted; account kept. Credit held for a possible hosted AI mode after launch, if it hasn't expired by then. |
| PyPI `biasclear` | New project account on the project mailbox | **Claimed by publishing, not by a pending publisher.** PyPI's docs say a pending publisher doesn't reserve a name. A small working release goes out within days of the new repo existing. The project is never deleted, only archived, because the preprint's install line is permanent. |
| npm `@biasclear` | Later (after launch) | npm Trusted Publishing can't make a first publish, so the first npm release gets its own plan when it's needed. |
| AI accounts | Not needed before launch | See §4. AWS is optional and read-only for now. |

---

## 4. The AI layer (after launch)

**Launch ships rules only.** The checker, the Field Guide and the benchmark are all deterministic and need no AI account, key or bill. The AI layer is post-launch work, planned now so the choices are settled.

**Model: Claude Opus 5.5 (`claude-opus-5-5`)**, the owner's pick. It costs $4 per million input tokens and $20 per million output tokens. Thinking can't be turned off, and thinking tokens bill as output, so a second-opinion check costs a few cents, not the 1.8 cents revision 1 claimed. The real number gets measured by a script before any page quotes it. Refusals come back as ordinary responses (`stop_reason: "refusal"`), so the UI must handle them.

| Mode | What | When |
|---|---|---|
| **A. Rules only** | Deterministic checker in the browser | Launch |
| **B. Bring your own key** | The visitor's own Anthropic key calls Anthropic straight from their browser | After launch, with its own security spec (below) |
| **C. Hosted second opinion** | A small server calls the AI for visitors without a key | Only if people ask, and only after rewriting the privacy rule to allow it as a labeled opt-in |

**Mode B security spec** (required before it ships):
- The key box and the AI call live on a separate origin (for example `ai.biasclear.com`) with no analytics or third-party scripts. The main page talks to it by `postMessage` with exact origin checks.
- Strict Content-Security-Policy on that origin: connections only to `api.anthropic.com`, no inline scripts, and framing only by biasclear.com.
- The key is kept in memory by default, with no localStorage, cookies or URL. There's a visible Forget key button. Visitors are told to use a dedicated, spend-limited key.
- Model output is rendered as text, never as HTML.
- The `anthropic-dangerous-direct-browser-access` header is recorded as an accepted risk: bring-your-own-key only, never a project key.

**Mode C honesty.** Mode C sends the visitor's text to a server we run and to Anthropic. That breaks today's "your text never leaves the tab" rule, so the rule and the page copy must change first, and the switch must say plainly where the text goes. We'd store nothing, but Anthropic's API retention policy applies. The $50 workspace limit is the real abuse control, and when it's hit the feature pauses for everyone.

**Internal AI jobs** (a blind labeler for the in-house test set, red-team sweeps):
- Use the Anthropic API from GitHub Actions through Workload Identity Federation (keyless), in a spend-limited workspace.
- The trust rule is scoped to the `biasclear/biasclear` repo, the `main` branch, one workflow file and a protected environment, so no agent-pushed branch can mint credentials.
- This needs an Anthropic Console account, which is a post-launch owner step.

**AWS.** The old account is suspended. Claude on Bedrock bills through AWS Marketplace, and ordinary promotional credits usually don't cover Marketplace charges. The owner's only AWS step for now is reading the bill and the credit terms, and adding **no card**. The plan doesn't depend on AWS.

---

## 5. Security model

| Threat | Control |
|---|---|
| A squatter takes `pip install biasclear` (the preprint and the old Action point there) | Delete the Action now. Claim the name by publishing a real release within days. Never delete the PyPI project. |
| The domain claimed on Render after the services are deleted | Remove the custom domains and the Namecheap DNS records in the same sitting as the deletion |
| Old keys and data surviving | Delete **both** Render services and any environment groups; delete the old AWS access key after reading the bill; the Gemini key is already deleted |
| A secret committed | Pinned secret scanner plus a custom rule for BiasClear-style keys (`bc_…`); checkout without persisted credentials; `AGENTS.md` hard rule |
| An agent loosening its own rules | Protected paths are merged by the owner only; the ruleset requires checks and allows no bypass; the PM never edits rulesets |
| Keyless CI tokens misused | OIDC trust scoped to repo + branch + workflow + protected environment |
| Personal data republished | The new repo is seeded from a scrubbed snapshot built with `git archive`, never a working folder, after a grep gate for personal identifiers |
| Replies exposing a personal inbox; spoofed mail to exposed signups | Real project mailbox with SPF, DKIM and DMARC |
| Account takeover | Two-factor (authenticator app) on Namecheap, GitHub, Render, PyPI and the mailbox. Recovery through the project mailbox, and the domain stays renewed while that's true. |
| Rules that tilt politically | Structural rules only; 120+ swapped pairs as a required check; red-team pairs added as tests |
| Inaccessible design | WCAG 2.2 AA: every result is also available as a keyboard-reachable list; tier is never shown by color alone; contrast is checked by a script against the design tokens |

---

## 6. Moving to the new organization (safe order)

GitHub can't transfer issues between different owners, deleting a repo can't be undone, and the published preprint links to `github.com/bws82/biasclear`. So the move goes in this order:

1. **Owner:** check that `github.com/biasclear` is free, create the free organization, and create the empty public repository `biasclear` inside it. The Claude GitHub App can push but can't create repositories.
2. **Owner:** install the Claude GitHub App and the ChatGPT Codex connector on that organization.
3. **PM:** build the seed snapshot with `git archive` from `main`. Scrub personal data from the tree (the bio, location, employer, LinkedIn, personal email, `funding.json`, the Sponsors link, `pyproject` authors). Run a grep gate. Push it as the first commit of `biasclear/biasclear` with the approved blueprint, the rulebook and the chosen license.
4. **PM:** recreate issues #18 to #20 there. Close the five stale dependabot PRs. Open the release workflow for PyPI.
5. **Owner:** create the `pypi` environment with the owner as its required reviewer, so every release waits for the owner's Approve click. Then turn on the `main` ruleset in the new repo once CI has run there once: require the four checks, block force pushes and deletions, no bypass, and zero required approvals.
6. **Access test:** a Codex draft PR, a red-team review and a PM-opened PR must all work in the new repo before anything old is deleted.
7. **PM:** export the old repo's full history and PR discussions into one archive file in the owner's private Drive folder. It never goes to GitHub.
8. **Owner:** add a related link on the Zenodo record's metadata pointing to the new repo. This is a metadata edit only: no new version, no new DOI.
9. **Owner:** delete `bws82/biasclear` (confirm it still has 0 forks). Then create a new public `bws82/biasclear` with a single README: "BiasClear moved to github.com/biasclear/biasclear". Archive the stub.
10. **Owner:** update the profile README link and add a dated note to the EA Forum post withdrawing the v1 claims.

Copies of the old history in third-party archives (for example, Software Heritage) are outside our control. Deleting the repo limits exposure but can't erase them. The owner's `bws82` account must never be renamed or deleted, because the stub and the preprint depend on it.

---

## 7. Build order and dates

| Phase | Work | Target |
|---|---|---|
| 0 | Owner sittings 1-4; new org and repo seeded; PyPI name claimed; Render and DNS cleaned up | **Oct 9** |
| 1 | E1 rule pack, E2 browser engine, E3 symmetry | **Oct 30** |
| 2 | Lightbox site on GitHub Pages, staging URL for the owner | **Nov 6** |
| Go/no-go | Owner reviews staging | **Nov 9** |
| **Gate A** | Launch | **Week of Nov 16** |
| After launch | Mode B, share cards, poster, in-house labeled set, PIT v2 preprint, npm, MCP server | — |
| **Gate B** | Keep going or shelve | **Feb 1, 2027** |

**Launch floor** (ships even if everything else slips):
- the mode A checker
- the Field Guide
- a Method page, with published benchmark numbers or an honest "not measured yet"
- Privacy
- About

**Slip rule:** if the Nov 9 go/no-go fails, set one new launch date and move Gate B to about 10 weeks after launch.

**Benchmarks.** E4 uses public, externally labeled datasets. SemEval propaganda data usually requires registration and a research-use agreement, so the PM checks each dataset's terms. Where registration needs a person, it's a 5-minute owner click, and the data is never redistributed. The in-house labeled set is self-graded however carefully it's built, so it's published as secondary evidence and labeled that way.

**PIT v2 preprint.** It goes out under the owner's name, so it needs his full read and a stated AI-assistance note first. That's after launch.

---

## 8. Shelving (if Gate B says stop)

In this order:
1. Move every project account's recovery email off the domain.
2. Archive the repo, leaving the PyPI project in place.
3. Leave the stub and the preprint links working.
4. Then let the domain lapse, or keep it for about $20 a year to prevent squatting.

---

## 9. Owner decisions (answered 2026-09-27)

1. **Blueprint revision 2:** approved.
2. **License:** Apache-2.0 for the code, CC BY 4.0 for the rule pack.
3. **Signup notice:** one short email to the affected signups, plus a public note; the list is deleted after sending. Draft in `ops/SIGNUP_NOTICE.md`.
4. **Project mailbox:** Namecheap Private Email, Launch plan (about $15 a year; 30-day free trial).
