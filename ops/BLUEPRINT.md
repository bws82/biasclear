# BiasClear v2 blueprint

Owner: the project owner. Author: the PM (Claude). Status: **approved**. The owner approved revision 2 on 2026-09-27. This is **revision 3, 2026-09-27**. It takes effect when the owner merges it.

Revision 2 came from a red-team pass by six separate Claude reviewer sessions. Revision 3 adds an overnight audit of revision 2 (two skeptics checked each finding), primary-source research on nine open questions, and the PM decisions that settle them. The owner's steps live in his private checklist (the Owner Console). This page is the reasoning behind them.

Nothing is decided unless it's written here. Changing a decision means changing this page first.

## What changed in revision 3

- **You create the new repository with a README.** The PM's clean code arrives as a "seed" pull request, and you merge it. The Claude app can't create repositories, and it can only push its own branch.
- **The release switch is set before the seed merges.** Every PyPI release waits for your Approve. That Approve is the one owner gate GitHub itself enforces. Until the access test shows the PM can create tags, you also create each release tag (two clicks in all).
- **Codex starts from one comment on the ticket.** Its handle appears only in the PM's trigger comments, because any mention from your account starts a paid task. If the trigger fails, a short fallback ladder applies (§2).
- **biasclear.com is locked to the GitHub organization** by a TXT record in Sitting 2, so no one else can point a GitHub site at it. The same day as the Render sitting, the domain is pointed at Pages and shows a one-page placeholder until launch. The short gap in between, when biasclear.com shows nothing, is accepted (a refinement of decision 15).
- **Mailbox:** a paid year, not the trial, with its own auto-renew. DMARC (the anti-spoofing record) starts at watch-only (`p=none`) and moves to `p=quarantine` after 2 to 4 weeks of clean reports. `p=reject` comes later, if ever, as your choice. The signup note waits on the mailbox test, not on DMARC.
- **The Render sitting has a fixed order.** One paste into Render's web Shell, done live with the PM, is the single exception to "no terminal".
- **The security table has new rows:** domain takeover on GitHub Pages, faked checks, auto-created environments, handle-triggered paid tasks and injected script. Controls that aren't built yet say so.
- **The first PyPI release (2.0.0a1) has written contents,** and the access test now covers every step nobody has proven yet.
- **Dates:** the domain auto-renews around Jan 19, 2027 (about $15), before Gate B. Shelving now removes the site's DNS records first.
- **The owner playbook and the unsent signup draft are private** (decision 25). Account security, recovery design and the Render order live in the owner's private checklist, and the new repo's seed carries neither file.
- **The signup note goes to everyone on the list,** by about Oct 26 (§9).

---

## 1. Principles

1. **Measure before cutting.** No build ticket starts until this page and the ticket agree.
2. **Store nothing worth stealing.** The launch product runs in the visitor's browser: no server, no database, no user data, no secrets. This is a design goal with named exceptions: GitHub, as the host, logs visitor IP addresses (the Privacy page says so), and the AI modes in §4.
3. **No stored credentials where a keyless option exists.** Publishing and CI use short-lived GitHub identity tokens (OIDC), scoped to one repo, one workflow and one environment. For PyPI, that environment accepts only release tags and waits for the owner's Approve click (§6).
4. **Every public number is produced by a script in the repo.** If the script isn't there, the number isn't published.
5. **The owner holds the keys; agents hold the tools.** Accounts, passwords, two-factor, payment methods, deletions and release approvals are the owner's clicks. Owner steps are **web clicks and decisions only**: no terminal, no code, at most 30 minutes per sitting, at most 2 hours a week. **One recorded exception:** in the Render sitting, the owner pastes one PM-provided export line into Render's web Shell, live with the PM (§6).
6. **Accessible to everyone.** WCAG 2.2 AA is a launch requirement, not polish.

---

## 2. Who does what

| Role | Who | Does | Never does |
|---|---|---|---|
| Owner | The project owner | Vision, gate approvals, account security, payment, deletions, merges on protected paths, release tags and approvals | Terminal work (one exception, §1), code review |
| PM | Claude | Plan, tickets, design, code review, merges on unprotected paths, starts Codex tasks | Create accounts or repos, spend money, change settings or rulesets, approve deployments, merge protected paths |
| Builder | Codex | Implements tickets as PRs | Merge, touch accounts or settings, edit `AGENTS.md` or rulesets |
| Red team | A separate Claude session the PM starts on every ready PR; Jarvis (GPT) at gates, relayed by the owner | Attack changes and public claims | Write product code, merge |
| Memory | The owner's private notes vault | Project history the PM reads before big decisions | Nothing (read only) |

**One GitHub identity, one enforced gate.** Claude, Codex and the owner all act through the owner's GitHub account, so GitHub can't tell them apart. That means:
- **Code-owner review can't be enforced by GitHub.** GitHub won't let an account approve its own PR, so the ruleset on `main` requires status checks, not approvals.
- **Owner-only merges are a process rule, not a GitHub control.** The PM never merges a PR that touches a protected path (`AGENTS.md`, `CLAUDE.md`, `LICENSE`, `README.md`, `.github/`, `ops/BLUEPRINT.md`). For those, the PM posts a plain-language summary, and the owner clicks Merge. A PR can change the workflow that runs its own checks, so the owner's read of any `.github/` change is what protects CI. Merges to `main`, and so site deploys, are not gated by GitHub. The PM batches protected merges into one list about once a week; anything that gates a date or a security step goes to the owner the same day.
- **The one gate GitHub enforces is the release approval.** The Claude GitHub App has no Administration, Deployments, Environments, Secrets or Pages permission. So no Claude session can change a setting or approve a protected deployment, even though it acts as the owner.
  - Never connect GitHub through `/web-setup`, and never put a GH_TOKEN in the cloud environment. Either would replace the app's token with a broader one.
  - The owner declines any future app permission request for those five.
  - Whether the Codex connector holds Deployments is unverified. The owner checks its permission list at install.
- **Signatures label, they don't authenticate.** Every agent post ends with a role line (`— Codex (builder)`, `— Red team`, `— Claude (PM)`). A post from the owner's account proves nothing about who wrote it, because every agent posts as that account. Owner approvals count only when the owner gives them to the PM in his own chat, or as his own Merge or Approve click. A GitHub comment saying "approved" is never an owner approval.
- **The PM can't read GitHub's alert lists** (secret scanning, code scanning, Dependabot). It relies on CI job logs, and the owner forwards any alert email.
- **Later, optional:** a separate machine account for agents would let GitHub enforce owner review. It costs the owner a second account and reconnecting both agents, so it waits until the workflow proves itself.

**How Codex gets work.**
- **Start:** the PM starts each ticket with one comment on the ticket issue itself: the Codex handle, then "implement this issue per AGENTS.md. Open one pull request against main, fill every section of .github/pull_request_template.md, and put `Closes #N` in the body. — Claude (PM)". There is no stub PR. Codex picks its own branch.
- **Checks:** a bot reply or an eyes reaction within about 2 minutes, and a PR that references the issue within about 60 minutes. The PM checks open issues and PRs on a schedule, several times a day, rather than waiting for notifications.
- **Fallback ladder, in order:**
  1. Repost once.
  2. If the reply says "create an environment", check the owner's Codex environment step. It may also be the known bug openai/codex#20093.
  3. If the task finished but no PR appeared, the owner opens the "View task" link and clicks Create PR.
  4. Otherwise the owner starts the task at chatgpt.com/codex with one fixed line the PM supplies.
- **Still broken after 24 hours:** the owner chooses among a Claude Code builder session the PM starts (this loses the second model family), the Codex agent in a paid Copilot plan (any paid plan; it runs as its own GitHub app), or codex-action with an OpenAI API key. That question sits on the board's owner list.
- **Follow-ups on a Codex PR:** one comment on the PR asking Codex to address the blocking findings, then confirm that the PR's head commit changed. If it didn't, or Codex says it couldn't push (known bugs openai/codex#38351 and #47223), the PM re-triggers on the issue for a replacement PR and closes the old one.
- **Why the access test decides:** starting Codex from an issue comment worked on bws82/biasclear #18 to #20, but OpenAI doesn't document it now, so it could change without notice.
- **Prerequisites (owner steps):** the Codex connector on the organization (Sitting 2), plus a Codex environment for `biasclear/biasclear` and Codex code review set to explicit mentions only, never "Smart detect" (Sitting 3, after the seed merges).

**Handle rule (all agents).** The Codex handle appears only in the PM's trigger comments: the one start comment per ticket, and one follow-up comment on the PR per round of blocking findings (each a new comment). Nowhere else: issue and PR bodies, reviews, summaries, relayed red-team posts, or docs quoted in comments. (This page writes "the Codex handle" for that reason.) Any appearance in a comment from the owner's account starts a paid task, even inside backticks. On 2026-09-27, three PM comments that quoted the handle in backticks each started a task. Write "Codex" without the @, and never edit an old comment to add the handle.

**How the red team works.**
- The standing red team is a separate Claude session the PM starts on every ready PR. It gets the ticket, the raw diff and `AGENTS.md`, not the PM's summary. It shares the PM's model family and operator, so it isn't independent of the PM; it is a different vendor from Codex, the builder.
- It posts one `RED TEAM:` review as a **Comment** review, because the author and reviewer are the same account and Approve or Request changes won't work. Each finding is marked **blocking** or **note**. The verdict is one of two labels: `redteam:clear` or `redteam:blocking`.
- Codex answers each blocking finding with `fixed in <sha>` or `dispute: <reason>`. The red team re-reviews once, limited to the open findings and the fix commits. The PM decides anything still open in a signed comment with a one-line reason. An override that touches rules, symmetry pairs, benchmark output or public copy waits for the owner.
- The PM merges an unprotected-path PR only with `redteam:clear` and green checks. For a protected path, the PM's summary shows the verdict, and the owner doesn't merge on `redteam:blocking`.
- Dependabot PRs get no red-team pass. The PM checks CI and the release notes; bumps that touch `.github/` go on the owner's merge list.
- Every asymmetric pair any reviewer finds becomes a permanent test case, or a logged dispute with the PM's reason. Disputes are listed for the owner at Gate A.
- **Jarvis (GPT)** is the outside check at gates, starting with the Nov 9 go/no-go (about 10 minutes of that sitting). The PM prepares one link and one prompt. The owner pastes them into ChatGPT and passes the answer back. The PM posts it in a quote block labeled "Jarvis (GPT) review, relayed by the owner", unedited except that any Codex handle loses its @. The PM never signs as Jarvis.

---

## 3. Accounts map

| Asset | Where | Status / next |
|---|---|---|
| Domain `biasclear.com` | Namecheap | Paid to Feb 18, 2027. Sitting 1: two-factor, auto-renew and domain privacy on, with a payment card saved. Auto-renew charges about 30 days early (around Jan 19, 2027, about $15), before Gate B. Accepted: a lapse costs more. Recovery design: in the owner's private checklist. |
| DNS | Namecheap | Today `@` and `www` still point at Render. The Render sitting deletes those two records **before** the Render domains are removed. Kept for good: the organization's Pages verification TXT record `_github-pages-challenge-biasclear` (Sitting 2). Mail: MX and SPF come from Mail Settings (never add a second SPF), DKIM at `privateemail._domainkey`, and DMARC. Once Render is gone and the placeholder is deployed to Pages (its PR merged before the Render sitting): set the custom domain in the repo first, then add GitHub's four A and four AAAA records on `@` and a `www` CNAME to `biasclear.github.io`, then Enforce HTTPS. No wildcard records. |
| Project mailbox `hello@biasclear.com` | Namecheap Private Email, Launch plan (one mailbox) | Sitting 4. A paid year, not the trial. Auto-renew on for the mail subscription, which is a separate switch from the domain's. Aliases: today's forwarding addresses plus `dmarc`. Two-factor if Namecheap offers it; if not, that's recorded. DMARC starts at `p=none` and moves to `p=quarantine` after 2 to 4 weeks of clean reports; `p=reject` only later, if ever, as the owner's choice (it can break mailing lists). Recovery design: in the owner's private checklist. |
| GitHub organization and repo | Organization `biasclear`, repo `biasclear/biasclear` | Sitting 2: the owner creates both, the repo with a starter README. Seeded by a PR the owner merges (§6). Domain verified, two-factor required for members, code review limited to people with access. |
| Old repo `bws82/biasclear` | The owner's personal account | Frozen after the seed. Becomes a one-file stub pointing to the new repo, because the published preprint links there (§6). The `bws82` account is never renamed or deleted. |
| `bws82/biasclear-action` | Old GitHub Action | **Delete first** (Sitting 1). It runs `pip install biasclear`, and the first release claims that name. Nothing depends on it (GitHub code search: 0 users). A backup is in the owner's private Drive folder. Never recreated, not even as a stub. |
| Website | **GitHub Pages** on `biasclear/biasclear`, source GitHub Actions (Sitting 3) | Free, with soft limits of 100 GB a month and a 1 GB site. No extra vendor, no deploy secrets. From the `pages` step (the same day as the Render sitting, right after it) until launch day it serves a one-page placeholder. GitHub logs visitor IP addresses, and the Privacy page says so. Pages can't send response headers (no CSP `frame-ancestors`, no HSTS header). |
| Render | Existing account | Render sitting, with the PM live: two-factor first, then both v1 services (`biasclear` and `biasclear-api`) deleted. The account is kept. Its credit (amount and expiry confirmed in that sitting) is held for a possible hosted AI mode after launch. |
| PyPI `biasclear` | Project account on hello@ (username `biasclear`, fallback `biasclear-project`) | Sitting 5, after the mailbox test passes. Two-factor (passkey recommended, authenticator app as backup) with recovery codes kept offline. Recovery design: in the owner's private checklist. The name is claimed at the first approved release's token exchange, not by the pending publisher (PyPI's docs: a pending publisher doesn't reserve a name). First version 2.0.0a1, never 0.x or 1.x: the old project's filenames are burned. Never delete the project, a release or a file; yank instead, and archive at end of life. The preprint's install line is permanent. |
| npm `@biasclear` | Later (after launch) | npm Trusted Publishing can't make a first publish, so the first npm release gets its own plan. The scope isn't reserved before then. Accepted risk. |
| The owner's claude.ai and ChatGPT accounts | The owner's existing subscriptions | Needed now. They hold the Claude app and the Codex connector and act as the owner's GitHub account, so they are part of the deploy chain. Sitting 1: two-factor on ChatGPT, and on the account Claude signs in with. |
| Anthropic API | Not needed before launch | See §4. |
| AWS (v1 Bedrock) | Old root account, inactive | Not used by v2. Optional owner step: read the bill and credits, add no card, and delete every access key (root and IAM users). If the console blocks that, the keys stay unusable while the account is inactive, and deleting them is the first step of any reactivation. |
| PIT preprint record | Zenodo, DOI 10.5281/zenodo.18676405 | Gets a related link to the new repo when the old repo retires (metadata only, same DOI). Whether this DOI is the version DOI or the concept DOI is unverified. The owner reads both off the record page before any page relies on one. |

---

## 4. The AI layer (after launch)

**Launch ships rules only.** The checker, the Field Guide and the benchmark are all deterministic. The product needs no AI API account, key or bill; the build runs on the owner's existing Claude and ChatGPT subscriptions. The AI layer is post-launch work, planned now so the choices are settled.

**Model: Claude Opus 5.5 (`claude-opus-5-5`)**, the owner's pick. Listed price (unverified as of 2026-09-27): $4 per million input tokens and $20 per million output tokens. Also unverified: that thinking can't be turned off (effort as the only control, default `medium`) and that thinking tokens bill as output. The PM checks Anthropic's current pricing and model pages, and cites them with a date, before any of this is relied on. The cost per check is unmeasured. A script measures it before any page quotes a number.

**Refusals.** A declined request comes back as an ordinary response (HTTP 200) with `stop_reason: "refusal"`. Every caller follows these rules:
- Branch on `stop_reason`. `stop_details` is filled only for refusals, and its category can be empty.
- A `refusal` or `max_tokens` stop is a failed item. The UI shows it as declined and discards any partly streamed text. Scripts (the labeler, red-team sweeps, the cost script) record it as refused and count it. They never drop it or treat it as a clean result.
- Prompts ask for analysis of the pasted text, never for the model's own reasoning, which can be declined.
- Server-side fallbacks would run a different model than the owner's pick (and in mode B would bill the visitor's key). Whether to use them is an owner decision, recorded in the mode B and C specs.

| Mode | What | When |
|---|---|---|
| **A. Rules only** | Deterministic checker in the browser | Launch |
| **B. Bring your own key** | The visitor's own Anthropic key calls Anthropic straight from their browser | After launch, with its own security spec (below) |
| **C. Hosted second opinion** | A small server calls the AI for visitors without a key | Only if people ask, and only after rewriting the privacy rule to allow it as a labeled opt-in |

**Mode B security spec** (required before it ships):
- **Host first.** GitHub Pages can't send response headers, and browsers ignore `frame-ancestors` in a meta tag. So the host for the key origin (for example `ai.biasclear.com`) is decided before this spec is final: either a host that can set headers, or a popup design (not an iframe) with framing recorded as an accepted gap. Either way, the PM checks the live response headers before mode B ships.
- The key box and the AI call live on that separate origin, with no analytics or third-party scripts. The main page talks to it by `postMessage`, with exact origin checks both ways.
- Strict Content-Security-Policy on that origin: connections only to `api.anthropic.com`, no inline scripts, and framing only by biasclear.com where the host allows it.
- The key is kept in memory by default, with no localStorage, cookies or URL. There's a visible Forget key button. Visitors are told to use a dedicated, spend-limited key.
- Model output is rendered as text, never as HTML.
- The `anthropic-dangerous-direct-browser-access` header is recorded as an accepted risk: bring-your-own-key only, never a project key.
- The Privacy page says the text goes to Anthropic under the visitor's own key and account, and that Anthropic's retention policy applies.

**Mode C honesty.** Mode C sends the visitor's text to a server we run and to Anthropic. That breaks today's "your text never leaves the tab" rule, so the rule and the page copy must change first, and the switch must say plainly where the text goes. Anthropic's API retention policy applies, and anything the service keeps (such as a per-visitor counter) is named on the Privacy page.

**Mode C abuse and cost spec** (required before any mode C ticket opens; it ships in the same owner-merged PR that rewrites the privacy rule):
- A per-request ceiling: an input length cap, a fixed `max_tokens` and an explicit effort, with the worst-case cost per call taken from the cost script.
- A daily budget inside the service that fails closed to mode A with a plain message, so one bad day can't empty the monthly limit.
- Per-visitor limits, described honestly as weak against rotating addresses.
- Bot friction only if needed, and self-hosted (no third-party scripts).
- Its own spend-limited workspace with rate limits and spend alerts. The owner checks the organization's rate-limit tier before mode C ships. The $50 workspace limit is the last backstop: when it's hit, the feature pauses for everyone.

**Internal AI jobs** (a blind labeler for the in-house test set, red-team sweeps):
- They use the Anthropic API from GitHub Actions through Workload Identity Federation (keyless), in a spend-limited workspace with the narrowest scope.
- **Trust rule.** A job that uses an environment gets the subject `repo:<owner>/<repo>:environment:<name>`, not the branch form. So the rule matches the subject for one environment (`ai-jobs`) exactly, with no trailing `*`. Its claims pin `ref` to `refs/heads/main`, the repository owner, and `workflow_ref` to the one workflow file. The token lifetime is set to about 10 minutes. The PM reads the exact values from one dry-run token (decoded claims only) before the owner creates the rule, and never loosens the subject to get past an error.
- The `ai-jobs` environment allows deploys from `main` only. Required reviewers would add nothing here, because agents act as the owner.
- The workflow runs on manual dispatch or a schedule and grants `id-token: write` to that one job. It never sets `ANTHROPIC_API_KEY` or `ANTHROPIC_AUTH_TOKEN`, not even empty, because either would outrank federation.
- Code merged to `main` runs with this credential, so the scope and the spend limit are what cap the damage. The rule is created only after the `main` ruleset is on.
- This needs an Anthropic Console account, which is a post-launch owner step. The labeled set's design rules are in the board (Track 2).

**AWS.** The old account is inactive. Claude on Bedrock bills through AWS Marketplace, and ordinary promotional credits usually don't cover Marketplace charges. The owner's AWS steps are optional: read the bill and the credit terms, add **no card**, and delete every old access key (§3). If the account is ever reactivated or reopened, deleting every key and the v1 IAM user comes first. The plan doesn't depend on AWS.

---

## 5. Security model

"Planned" marks a control that isn't built yet, with where it lands.

| Threat | Control |
|---|---|
| A squatter takes `pip install biasclear` (the preprint and the old Action point there) | Delete the Action (Sitting 1). Before each PyPI owner step, the PM looks up `biasclear` in PyPI's simple index and stops if a project appears that isn't ours. The pending publisher names the repo, `release.yml` and environment `pypi`. The name is claimed by a working 2.0.0a1 release, not a placeholder. Never delete the project, a release or a file. If the name is squatted: report it (malware or PEP 541) and pick a fallback name the same day. |
| biasclear.com claimed on Render after the services go | In one sitting: delete the Namecheap `@` and `www` records first, then remove the custom domains in Render, then delete the services. Check every Render project and workspace. Never point a name at `*.onrender.com` again. |
| **biasclear.com taken over on GitHub Pages** | The domain is verified for the organization (TXT record kept for good) before any record points at GitHub. The custom domain is set in the repo before the A, AAAA and CNAME records exist. No wildcard records. At shelving, those records go before Pages or the repo does (§8). |
| Old keys and data surviving | Before v1 resumes for the export, the app is neutralized (empty audit database path, rotated keys). Both Render services, their disks and any environment groups or Blueprints are deleted. That removes only Render's copy of any key: the old AWS keys are deleted in AWS (§3). The Gemini key is already deleted. |
| A secret committed | **Planned, in the seed PR:** the scanner pinned by commit and version; reports of verified, unverified and unknown results; a bounded custom rule for BiasClear-style keys; read-only workflow permissions; checkout without persisted credentials. The PM runs the same scan on the seed before opening the PR. GitHub secret scanning and push protection are on (Sitting 3). The PM reads CI job logs, and the owner forwards alert emails. `AGENTS.md` hard rule. |
| An agent loosening its own rules | **Process only, not enforced by GitHub** while agents share the owner's account: the PM never merges protected paths or edits rulesets, and no agent opens Settings. **Enforced by GitHub:** the Claude app has no Administration permission (checked at install), so it can't edit rulesets or settings; required checks; an empty bypass list. The Codex connector's permissions are checked at install. Detection: the owner looks over the ruleset and recent protected-path merges at each gate. |
| **A required check faked** (anyone with write access can post a passing status named `test` through the API) | Each required check is pinned to GitHub Actions as its source. A PR that edits its own workflow is caught only by the owner's read of `.github/` changes (process). |
| **An unprotected environment created automatically** (GitHub creates a missing environment, with no protection, the first time a workflow names it) | The owner creates `pypi` (owner as required reviewer, admin bypass off, `v*` tags only) in Sitting 3, before the seed that names it merges. The Pages environment is checked for `main`-only deploys after its first run. |
| Keyless release tokens misused | PyPI trusts only this repo, `release.yml` and environment `pypi`. That environment takes tags only and waits for the owner's Approve. No Claude session can approve, because the app has no Deployments permission. "Prevent self-review" stays off, because releases run under the owner's account. |
| **A paid Codex task started by accident** | The Codex handle appears only in the PM's trigger comments (§2). Codex code review is set to explicit mentions, not "Smart detect". |
| **Script injected through pasted text or a link** | **Planned, site tickets:** user and model text reaches the page only as text, never as HTML; hostile-string tests; a strict meta-tag CSP on every page; share links carry no user text at launch; a local Semgrep rule inside the required `sast` job that fails on innerHTML, outerHTML, insertAdjacentHTML, document.write, DOMParser, createContextualFragment, srcdoc, eval and new Function in site and package code (no new required check). |
| Personal data republished | The seed is built from an explicit file list, never a working folder, and passes a gate for personal identifiers and withdrawn-claim phrases before the PR (§6). The same goes for `v1-final`. CI keeps only generic patterns, so the public repo never spells out the terms. |
| Old history with personal data | The old repo is deleted and replaced by a stub. Copies outside GitHub (other people's clones, code archives, public event archives) can't be erased, so the old personal email is treated as public. |
| **Old links hijacked through the `bws82` name** | The account is never renamed or deleted, because the preprint and the stub depend on it. Two-factor on. |
| Replies exposing a personal inbox; spoofed mail to exposed signups | Project mailbox with SPF, DKIM and DMARC. DMARC starts at `p=none` and moves to `p=quarantine` after clean reports. The notice waits on a passing mailbox test (SPF, DKIM and DMARC all PASS). |
| Account takeover | Two-factor on Namecheap, GitHub (required for organization members), ChatGPT, the account Claude signs in with, Render, PyPI (passkey recommended, authenticator app as backup), and the mailbox if offered. Recovery codes kept offline. Recovery design: in the owner's private checklist. The domain and the mail subscription are both on auto-renew. |
| Rules that tilt politically | Structural rules only. At least 120 swapped pairs (the symmetry script reports the real count), run inside the required `test` check. Red-team pairs are added as tests. |
| Inaccessible design | WCAG 2.2 AA: every result is also in a keyboard-reachable list, and tier is never shown by color alone. **Planned:** a contrast script against the design tokens, run inside `test` (B2); an automated accessibility check and one manual screen-reader pass before Gate A (S1). |

New CI jobs (for example the S1 accessibility check) become required when the owner adds them to the ruleset after their first green run on `main`. The TypeScript engine tests run inside `test`.

---

## 6. Moving to the new organization (safe order)

GitHub can't transfer issues between owners. A deleted repo can be restored only by its owner, within 90 days, and restoring may not work once the stub takes its name, so deletion is treated as final. The published preprint links to `github.com/bws82/biasclear`. So the move goes in this order. Sitting names match the Owner Console.

1. **Owner, Sitting 2:** check that `github.com/biasclear` is free, create the free organization, and create the public repo `biasclear` with "Add a README file" ticked (no license, no .gitignore). The Claude app can't create repositories or change settings, and a cloud session can push only its own `claude/...` branch, so `main` must already exist. In the same sitting: verify biasclear.com for the organization, require two-factor, and limit code review to people with access.
2. **Owner, Sitting 2:** install the Claude app and the Codex connector on the organization, with "All repositories", reading each permission list first (§2). The PM then attaches the new repo to its session with push access.
3. **Owner, Sitting 3, before the seed merges.** The seed carries a workflow that names `pypi`, and GitHub would create a missing environment with no protection. So first:
   - Create the `pypi` environment: required reviewer is the owner; "Prevent self-review" off; admin bypass off; deployments from tags `v*` only.
   - Set Actions to read-only, and don't let Actions approve PRs.
   - Turn on secret scanning, push protection, private vulnerability reporting and Dependabot alerts.
   - Set the Pages source to GitHub Actions.
4. **PM: the seed PR.** The PM commits the seed on top of the README commit, on its `claude/` branch, and opens the "seed" PR. (A PR needs shared history, and the PM can push only its own branch.)
   - **Contents: an explicit file list, never a working folder.** The v2 alpha package and its tests; a new README and CHANGELOG with the v1 withdrawal notice; `AGENTS.md`; `CLAUDE.md`; `ops/` except `OWNER_STEPS.md` and `SIGNUP_NOTICE.md` (private, decision 25; the old branch keeps a one-line pointer); `.github/` without `FUNDING.yml`; the license files (Apache-2.0 for the code, CC BY 4.0 for the rule pack). No v1 server or site, `docs/`, `funding.json`, `render.yaml`, Dockerfile, binaries or databases.
   - **Scrub:** personal data and withdrawn claims. Links to the project's home point to `biasclear/biasclear`; references to the old repo stay as they are. `pyproject` authors: "BiasClear contributors" <hello@biasclear.com>.
   - **Gate:** a case-insensitive search of every file, binaries included, for the owner's personal identifiers and for withdrawn-claim phrases, plus the pinned secret scanner. Allowed matches: the citation lines in the README and `AGENTS.md`, `@bws82` in CODEOWNERS, `bws82` in `ops/` where it names the old repo, stub or Action, and, in `v1-final` only, the leftover `github.com/bws82/biasclear` links (link rot, not personal data). The PM also reads every file under `ops/` for the owner's operational details. The PR summary records the source commit and "0 matches outside the allowlist".
   - **`.github/`:** hardened CI (§5), with the `security` check auditing what v2 ships. `release.yml`: triggered by `v[0-9]*` tags, `environment: pypi`, `id-token: write` on the publish job only, and the publish action pinned by commit. CODEOWNERS narrowed to the protected-path list and marked informational. Dependabot for GitHub Actions only, grouped monthly (the pip block goes with the retired API).
5. **Owner, Sitting 3:** merge the seed. The PM's plain summary lists every protected file it adds, `.github/` included. This merge is CI's first run on `main`. Then create the Codex environment for `biasclear/biasclear` (no secrets, agent internet off) and set Codex code review to explicit mentions only.
6. **Owner: ruleset `protect-main`,** right after the seed's checks pass on `main`, and before any agent merge or release. Enforcement Active; target the default branch; PR required with 0 approvals and code-owner review off; checks `test`, `security`, `secret-scan` and `sast`, each pinned to GitHub Actions; block force pushes; restrict deletions; empty bypass list. The PM reads the ruleset back through the API to confirm each field. No agent merges in the new repo until that check passes.
7. **PM:** create the labels (`agent:codex`, `track:engine`, `track:site`, `question-for-pm`, `redteam:clear`, `redteam:blocking`, `dependencies`, `ci`). Recreate the tickets from `ops/ISSUES_TO_RECREATE.md` (E1 closed as done, then E2, E3, E6, E4 and S1) as fresh issues, with no Codex handle in their bodies and no pointer to the old repo; start them one at a time after the access test. Close the stale Dependabot PRs. Open the PR for the Pages workflow and the one-page placeholder; the owner merges it (`.github/`) before the Render sitting. From the seed on, all work (plan docs included) happens in the new repo. On `bws82/biasclear` the PM only closes issues and PRs, each with a link to the new repo.
8. **Access test,** before anything old is deleted. It covers every step not yet proven:
   - The PM pushes its branch (including a `.github/workflows` change) to the attached repo and opens a PR.
   - The PM creates a label and an issue through the API, posts a comment and a Comment review, reads a job log, and dispatches and reruns a workflow.
   - The PM tries to create a tag through the API. If it can't, the owner keeps creating release tags on the Releases page.
   - One small test issue goes from the Codex start comment to a merged Codex PR. The test records whether Codex opened the PR itself or needed the owner's Create PR click.
   - The red team posts its review and label, and the PM merges that unprotected-path PR with `redteam:clear`.
   - The first release (step 10) shows the run waiting for the owner's Approve, with no way for an agent to approve it.
   - If the Codex path still fails after the fallback ladder and 24 hours, the owner picks the fallback (§2).
9. **`v1-final`:** after the seed merges, the PM builds the retired v1 code as an orphan commit from a recorded commit of old `main`. It passes the same gate and carries the withdrawal notice at the top of its README and CHANGELOG. The PM pushes it through its branch. The tag is created by the PM through the API if the access test shows it can, and otherwise by the owner on the Releases page. That tree has no release workflow, so its tag can't start a release even though it matches `v*`. v1 code, including this tag, stays under AGPL-3.0.
10. **First release (2.0.0a1), after the seed, the `protect-main` ruleset, Sitting 5 and the `v1-final` tag:** the PM posts the built files and their metadata. Unless the access test showed the PM can create tags, the owner creates the tag on the Releases page (Draft a new release → tag → target `main` → Publish release), then presses Approve and deploy. The name is claimed when that run exchanges its token. That's two owner clicks per release, both deliberate.
11. **PM:** export the old repo into one archive in the owner's private Drive folder: a mirror of every branch, tag and PR ref; all PRs and issues with their reviews and comments; release notes; and any Discussions or wiki pages. It never goes to GitHub.
12. **Owner, retire the old repo (after the access test):**
    - Zenodo: on the PIT record, click Edit (not New version). Under Related works add "Is supplemented by", `https://github.com/biasclear/biasclear`, scheme URL, type Software. Then click the green Publish; Save draft changes nothing public. The DOI stays the same. If the PM finds withdrawn claims on the record, a dated note the PM drafts goes into the same edit, and onto the SSRN abstract page too. The owner also checks for any software record Zenodo's GitHub link made from the old repo. The PM confirms the new link is live before the next step.
    - Delete `bws82/biasclear` (confirm it has 0 forks). Then create a new public `bws82/biasclear` with a single README that points to the new repo, the `v1-final` tag and the DOI. Archive the stub. Delete the old repo's Codex environment.
    - Update the profile README link, and add a dated note to the EA Forum post withdrawing the v1 claims.

The preprint's Data Availability link keeps working, because the stub sends readers to `v1-final`. Deep links to old files and commits will 404; the full history lives only in the private archive. Copies of the old history in third-party archives (for example, Software Heritage, and public event archives that hold commit emails) are outside our control. Deleting the repo limits exposure but can't erase them. The owner's `bws82` account must never be renamed or deleted (§5).

**First release contents (2.0.0a1).** The first release claims the name and stays public for good, so its contents are fixed here:
- A new minimal package: zero dependencies; no file writes, network calls or side effects on import; no truth score, audit, learning, LLM, API or certificate code.
- Rules: the v1 structural rules with the two named lists removed (the school list and the agency list), plus swapped-pair tests for institutions and credentials. If that can't be done in days, it ships fewer rules. The name claim doesn't wait for E3.
- Not a v1 1.2.x re-release, because v1 carries the withdrawn truth score and AI-SDK dependencies. v1 lives at `v1-final`.
- Metadata: authors "BiasClear contributors" <hello@biasclear.com>; homepage biasclear.com; repository links to `biasclear/biasclear`; a short description that says it's a pre-release rule set with no accuracy claims; license Apache-2.0 (plus CC BY 4.0 if the rule pack ships in the wheel), with the license files.
- Checks run on the built files, not just the tree: `twine check`, the personal-identifier gate, and a search for the withdrawn lists, `truth_score`, AGPL and `bws82`. Before the owner approves, the PM posts the wheel's file list and metadata.

### Render and DNS cleanup (one sitting, with the PM live)

**First, before Sitting 1:** a one-minute containment check (decision 28). If the old v1 server still shows its log, the owner suspends both v1 services in Render. Suspending is reversible.

One sitting with the PM live, after the mailbox works, because the signup list goes into a hello@ draft. The order is fixed for safety and lives in the owner's private checklist. One paste into Render's web Shell is the single exception to "no terminal". Before the owner removes the Render domains, the PM checks public resolvers (1.1.1.1 and 8.8.8.8) until neither returns Render's address or `biasclear.onrender.com` for biasclear.com or www, waiting out the TTL if needed. Deleting Render services removes only Render's copy of any keys; the old AWS keys are handled in AWS (§3).

Once the placeholder is deployed to Pages (its PR merged before the Render sitting) and the domain shows Verified, the owner points biasclear.com at Pages (§3, DNS row). The PM unlocks that step as soon as the Render sitting ends, and the owner does it the same day as its own short sitting. Between the two, biasclear.com shows nothing: old v1 links and the preprint's homepage link are dead for those few hours. That short gap is accepted as a refinement of decision 15.

---

## 7. Build order and dates

| Phase | Work | Target |
|---|---|---|
| 0 | Owner Sittings 1 to 5, the ruleset and the Render sitting; organization and repo set up and seeded; PyPI name claimed with 2.0.0a1; Render gone; placeholder page on biasclear.com | **Oct 9** |
| 1 | E1 rule pack, E2 browser engine (it emulates Python's `re` semantics, so both engines give identical results), E3 symmetry | **Oct 30** |
| 2 | Lightbox site built. The owner reviews it as a private preview (a claude.ai artifact, as with the homepage now), so nothing unlaunched is public | **Nov 6** |
| Go/no-go | Owner reviews the private preview; Jarvis's first review, relayed by the owner | **Nov 9** |
| **Gate A** | Launch: the Pages deploy switches from the placeholder to the site | **Week of Nov 16** |
| Retire old repo | Once the access test passes (§6, step 12) | Before Gate A |
| After launch | Mode B, share cards, poster, in-house labeled set, PIT v2 preprint, npm, MCP server | No date yet |
| Domain renewal | Auto-renew charges about $15, about 30 days early. Accepted | **About Jan 19, 2027** |
| **Gate B** | Keep going or shelve. Its renewal question is about the Feb 2028 renewal | **Feb 1, 2027** |

No Phase 1 PR merges in the new repo until the `protect-main` ruleset passes the PM's read-back.

**Launch floor** (ships even if everything else slips):
- the mode A checker
- the Field Guide
- a Method page, with published benchmark numbers or an honest "not measured yet"
- Privacy (it says GitHub, as host, logs visitor IP addresses, and that BiasClear runs no analytics)
- About

Gate A accepts an honest "not measured yet" on the Method page, the same as the launch floor.

**Slip rule:** if the Nov 9 go/no-go fails, set one new launch date and move Gate B to about 10 weeks after launch.

**Gate B signals.** BiasClear runs no analytics before Gate B. If Gate B needs a visit count, it uses a cookieless, self-evident method the owner approves first. Otherwise it uses signals that need no tracking script, such as stars, PyPI downloads, citations and messages to hello@.

**Benchmarks.** E4 starts with PTC (SemEval-2020 Task 11) from Zenodo record 3952415. It's an open download with no registration, reported as CC BY 4.0 (unverified). The fetch script checks the license and a checksum and stops on a mismatch. SemEval-2023 Task 3 is left out of launch numbers: its data agreement reportedly limits use to the shared task (unverified), so it returns only with the organizers' written permission. Data is never committed, uploaded as a CI artifact or printed in logs. Any data request goes from hello@ in the project's name, never under a false name. If an agreement must be signed by a named person, that's an owner decision recorded in §9.

**In-house labeled set** (after launch). It's self-graded however carefully it's built, so it's published as secondary evidence and labeled that way. Its design rules (a pre-registered, hashed guide; an agreement threshold before any number is published; only texts we may republish; refused items counted) are in the board's Track 2.

**PIT v2 preprint.** It goes out under the owner's name, so it needs his full read and a stated AI-assistance note first. That's after launch. It's posted with New version on the same Zenodo record: a new version DOI under the same concept DOI.

---

## 8. Shelving (if Gate B says stop)

In this order:
1. Move every project account's recovery email off the domain (PyPI, and any later project account).
2. Delete the Pages records (the A, AAAA and `www` CNAME records) before unpublishing Pages or archiving the repo. Keep the verification TXT record while the domain is held.
3. Archive the repo, leaving the PyPI project in place. Delete nothing.
4. Leave the stub and the preprint links working. The `bws82` account stays.
5. Turn off auto-renew for the mail subscription. Then decide the domain: to let it lapse, also turn off auto-renew for the domain and for Domain Privacy; or keep it for about $15 a year to prevent squatting. The Jan 2027 renewal will already have been charged, so this choice is about the Feb 2028 renewal.

---

## 9. Owner decisions (answered 2026-09-27)

1. **Blueprint revision 2:** approved. Revision 3 (this page) applies the overnight audit and research. The owner's merge approves it.
2. **License:** Apache-2.0 for the code, CC BY 4.0 for the rule pack. v1 code, including the `v1-final` tag, stays under AGPL-3.0. Known costs of the split: packages that ship the rule pack declare `Apache-2.0 AND CC-BY-4.0`, and CC BY grants no patent rights.
3. **Signup notice:** one email to everyone on the list (including post-March-20 signups), plus a public note. It goes from hello@ in BCC batches of 50 at most, after the export and a passing mailbox test (it does not wait on DMARC). Target: sent by about 2026-10-26. It says plainly that the v1 privacy page was wrong about what was stored or exposed; it sticks to facts and doesn't overstate. It adds one sentence on likely consequences, and says the list is deleted after sending; the list and the draft are deleted then. v2 gets one line pointing to the public note, nothing more. A dated private breach record is kept. If the list has more than about 250 addresses, or more than a handful at EU or UK domains, the owner decides on a privacy-lawyer consult before deletion. The draft stays private until it has been sent.
4. **Project mailbox:** Namecheap Private Email, Launch plan, about $15 a year, paid for one year (not the trial), with auto-renew on.

Open questions for the owner are in `ops/BOARD.md`, under "Questions for the owner": the Codex fallback if the access test fails, the desktop-folder intake that was dropped from the plan, and any other listing tied to BiasClear.
