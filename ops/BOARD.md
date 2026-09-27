# BiasClear v2 board

Status: revision 3, 2026-09-27. Maintained by the PM (Claude). Last updated: 2026-09-27.

**Blueprint:** [`ops/BLUEPRINT.md`](BLUEPRINT.md) settles accounts, keys, the AI model, hosting and agent roles. Build tickets follow it.
**Owner steps:** the owner works from his private checklist (the Owner Console). This board names owner steps by outcome only and links none of the checklist.

**Goal:** a free, browser-only persuasion checker whose numbers are measured and whose neutrality is tested on every release. It should feel remarkable the first time someone pastes text into it.

**Launch window:** week of November 16, 2026 (after the November 3 election). Phase 0 by Oct 9, engine (E1–E3) by Oct 30, staging site by Nov 6, go/no-go Nov 9.
**Launch floor:** mode A checker, Field Guide, Method (benchmark numbers or an honest "not measured yet"), Privacy, About. Everything else can slip past launch.
**Renewal:** the domain is paid to February 18, 2027. Auto-renew charges about $15 around January 19, 2027, before Gate B. That is accepted: a lapse costs more. Gate B's renewal question is about the February 2028 renewal.

## Questions for the owner

The PM doesn't decide these. Answer in chat whenever it suits you.

1. **Desktop folder.** The first night's plan had the PM read a folder of your earlier work from your desktop. It was dropped from the plan. Do you still want it?
2. **Other BiasClear items on your account.** Is there any other repository or listing tied to BiasClear (for example a funding listing) that you want kept or retired? The PM won't name or touch unrelated repositories.
3. **Codex fallback.** If the access test shows Codex can't be started from an issue comment, and it's still broken after 24 hours, which do you want?
   - a Claude Code builder session started by the PM (free, but the builder and reviewer are then the same model family);
   - Codex through a paid GitHub Copilot plan (any paid plan; it runs as its own app);
   - Codex run from a workflow with an OpenAI API key (paid per use, and a stored secret).

## Gates

| Gate | Passes when | Who approves |
|---|---|---|
| **A: launch-ready** | Symmetry suite green in Python and TypeScript. The Method page shows benchmark numbers made by a script, or an honest "not measured yet". Every public number traces to a script. The Privacy page matches the deployed site. Accessibility checks green, plus one manual screen-reader pass. The site passes the airtight checklist. Zero secrets in the tree. | Owner, at the Nov 9 go/no-go (Jarvis gives the outside check) |
| **B: keep going** (Feb 1) | At least one outside signal (educator, citation, researcher or journalist), or 50 stars. BiasClear runs no analytics, so a visit count (target about 1,000 checker visits) is used only if the owner first approves a cookieless, self-evident way to count. Otherwise: stars, PyPI downloads, citations and messages to hello@. The owner's time stayed within budget. | Owner |

## Tracks

### 0: Cleanup and claims
- [x] Withdraw v1 accuracy, neutrality and compliance claims (README, v1 docs marked archived)
- [x] LLM-proposed rules no longer auto-activate; human `approve()` required (v1, kept at `v1-final`)
- [x] Fix the README quick start (async) and the citation (v1, kept at `v1-final`)
- [x] Agent charter (`AGENTS.md`), PR template, this board
- [x] License decided (Apache-2.0 for the code, CC BY 4.0 for the rule pack) and applied in the seed commit (`LICENSE`, `rules/LICENSE`, `pyproject.toml`)
- [x] Branch protection: replaced by the `protect-main` ruleset in the new repo (track 0b). Nothing is set on `bws82/biasclear`.
- [ ] Strip the remaining v1 claim text: withdrawal notice at the top of the `v1-final` README and CHANGELOG; clear the old repo's description and homepage; set the new repo's description, homepage and topics with no "ai-governance" or "detection engine" wording
- [ ] No new tickets, branches or merges on `bws82/biasclear`. From the seed on, all work happens in `biasclear/biasclear`; on the old repo the PM only closes issues and PRs, each with a link.

### 0b: Move and cleanup (Phase 0, by Oct 9; order follows the Owner Console)
- [ ] **Owner, do this first:** check whether the v1 server still serves its log. If it does, suspend both v1 services (reversible).
- [ ] **Owner Sitting 1:** account safety; delete `bws82/biasclear-action` (already backed up to the private Drive archive)
- [ ] **Owner Sitting 2:** create the org `biasclear` and the public repo `biasclear/biasclear` with a README; lock biasclear.com to the org (TXT record, kept for good); install the Claude app and the Codex connector
- [ ] **PM: seed PR.** Built from an explicit file list, never a working folder. It carries E1 (rule pack and zero-dependency Python engine), hardened CI (pinned scanner, custom key rule, read-only permissions, no persisted credentials), narrowed CODEOWNERS, and Dependabot for GitHub Actions only. Before opening it, the PM runs the personal-data and withdrawn-claim gate and a full secret scan, and records the source commit and the gate output here. Owner merge.
- [ ] **PM: release workflow, per decision 8.** `release.yml` in the seed triggers on tags `v[0-9]*`. The publish job alone gets `id-token: write` and `environment: pypi`; the publish action is pinned by commit; no skip-existing. The release test job is named `release-test`, so it can't pass for the required `test`.
- [ ] **Owner Sitting 3:** create the `pypi` environment before the seed merges (owner as required reviewer, "Prevent self-review" off, admin bypass off, tags `v*` only); Actions read-only; security scanners on; Pages source set to GitHub Actions; merge the seed; create the Codex environment
- [ ] **PM: Codex environment clicks.** Send the owner the exact clicks: environment for `biasclear/biasclear`, no secrets, agent internet off, Codex code review set to explicit mentions only.
- [ ] **Owner: ruleset `protect-main`,** right after the seed's checks pass on `main`: Active, default branch, PR required with 0 approvals, checks `test`, `security`, `secret-scan` and `sast` each tied to GitHub Actions, no force pushes, no deletions, empty bypass list. The PM reads it back through the API. **No agent merges in the new repo until that read-back passes.**
- [ ] **PM: labels,** with a color and a one-line description each: `agent:codex` (#1D76DB), `track:engine` (#5319E7), `track:site` (#C5DEF5), `redteam:clear` (#0E8A16), `redteam:blocking` (#B60205), `dependencies` (#0366D6), `ci` (#BFD4F2). Before the access test: Dependabot won't create missing labels.
- [ ] **PM: access test** in the new repo. One small test issue goes the whole loop: the PM's start comment on the issue → Codex PR with `Closes #N` → red-team Comment review and label → PM merge of an unprotected path. It also checks:
  - whether the PM can create a tag through the REST API (one throwaway tag named `access-test`, which matches neither `v[0-9]*` nor `v*`; it is left in place and recorded here, not deleted, because AGENTS.md bars agents from deleting tags. Creating it needs the named exception in AGENTS.md "History" first). If it can't, the owner creates each release tag and `v1-final` on the Releases page;
  - that the Claude app token has no Administration, Deployments, Environments, Secrets or Pages permission;
  - that the PM can read a CI job log (its only source for secret findings).
  This is the go/no-go for the Codex path. If it fails, run the fallback ladder in decision 2, then Question 3 above.
- [ ] **PM: recreate the tickets** from `ops/ISSUES_TO_RECREATE.md` (in the seed): E1 opened and closed as done; then E2, E3, E6, E4 and S1. No Codex handle in any body and no pointer to the old repo. Start them one at a time, after the access test. Close each old issue with a "Moved to biasclear/biasclear#N" comment (no handle), as not planned. Close the stale Dependabot PRs.
- [ ] **PM: PR-sweep Routine** on `biasclear/biasclear`, right after the seed merges, so draft-to-ready changes and label events aren't missed.
- [ ] **PM: placeholder page plus Pages workflow** (owner merge: it touches `.github/`), merged before the Render sitting. Split build and deploy jobs; top-level `permissions: {}`; build job `contents: read`; deploy job `pages: write` and `id-token: write`; `environment: github-pages`; deploys from `main` only; actions pinned by commit (re-check at build time); no configure-pages step and no CNAME file. After its first run, the PM checks that the `github-pages` environment allows `main` only.
  - Placeholder text: BiasClear is being rebuilt; v1 accuracy, neutrality and compliance claims are withdrawn; code at github.com/biasclear/biasclear; contact hello@biasclear.com. No analytics and no third-party requests. A `404.html` with the same text, so old links such as `/demo` land on it.
- [ ] **Owner Sitting 4:** project mailbox hello@biasclear.com (paid Launch plan, auto-renew on, aliases including `dmarc`), mail records, DMARC at `p=none`, and the test mail an hour later (SPF, DKIM and DMARC all PASS)
- [ ] **PM: name watch** before each PyPI owner step and before the release tag: look up `biasclear` in PyPI's simple index. If a project appears that isn't ours, stop, report it (malware or PEP 541) and pick a fallback name the same day.
- [ ] **Owner Sitting 5,** after the mailbox test passes: PyPI account on hello@ and the pending publisher (project `biasclear`, owner `biasclear`, repository `biasclear`, workflow `release.yml`, environment `pypi`)
- [ ] **PM: `v1-final`.** After the seed merges, build the retired v1 code as an orphan commit from a recorded commit of old `main`, pass the same gate, and push it through the PM's branch. Tag it before `v2.0.0a1`, because the 2.0.0a1 README links to it. The PM tags it if the access test shows it can; otherwise the owner tags it on the Releases page.
- [ ] **First release, 2.0.0a1** (after the seed, the ruleset and Sitting 5). The PM posts the built files and their metadata. The owner creates tag `v2.0.0a1` on the Releases page (Draft a new release → tag → target `main` → Publish release), then presses Approve and deploy. The first release claims the name.
- [ ] **PM: private breach record** for the v1 signup list, dated, with no addresses: what, when, how many, and why there was no regulator filing. Kept private, next to the owner's checklist. Counts are added at the Render sitting.
- [ ] **Owner: Render sitting, with the PM live.** Fixed order, in the private checklist. The signup list goes straight into a draft in hello@'s webmail and nowhere else. The owner tells the PM only the count. If there are more than about 250 addresses, or more than a handful at EU or UK domains, the owner decides on a one-hour privacy-lawyer consult before the list is deleted.
- [x] **PM, done 2026-09-27:** replace `ops/OWNER_STEPS.md` and `ops/SIGNUP_NOTICE.md` on the branch with the one-line pointer from decision 25, keep their revision 3 text only in the Owner Console and the private Drive copy, and stop git from committing the local copies (skip-worktree or untrack). Earlier full versions of both files are already in the public history of `bws82/biasclear` (branch `claude/biasclear-revival-strategy-xvdgjm`); that can't be undone short of deleting the repo, which the retirement step does.
- [ ] **Owner: send the signup notice** (the draft stays private until sent). Unlocks after the export and a passing mailbox test. It does not wait on the DMARC policy. Target: sent by about Oct 26. BCC batches of 49 at most (hello@ in To makes 50). The PM logs the date and count here, with no addresses.
- [ ] **Owner: DMARC to `p=quarantine`,** 2 to 4 weeks after the mailbox test, once the reports look clean. `p=reject` only later, if ever, as the owner's choice: the mail standard warns it can break mailing lists.
- [ ] **Owner: point biasclear.com at GitHub Pages,** after the Render sitting, once the placeholder is deployed to Pages (its PR merged before the Render sitting) and the domain shows Verified. Best done in the next sitting after Render, so the domain isn't left without a site for long: custom domain set in the repo first, then 4 A and 4 AAAA records on `@` and `www` CNAME to `biasclear.github.io`, then Enforce HTTPS. No wildcard records.
- [ ] **PM: old-repo archive** into the owner's private Drive folder (every branch, tag and PR ref; issues and PRs with reviews; release notes). It never goes to GitHub.
- [ ] **Owner: retire the old repo** (after the access test): delete `bws82/biasclear` (0 forks), create the one-file stub at the same URL pointing to the new repo, `v1-final` and the DOI, archive the stub; delete the old Codex environment; Zenodo related link (Edit, Related works "Is supplemented by" the new repo, then Publish; the DOI stays the same); profile and EA Forum notes
- [ ] **PM: concept DOI.** Once the Zenodo concept DOI and v1 version DOI are confirmed, a ticket points "always current" PIT links at the concept DOI and keeps the version DOI where v1 is meant.
- [ ] **Owner, optional:** AWS bill and credits check, and delete the old access keys (or note that the inactive account blocks it)

### 1: Engine v2 (Codex builds, PM reviews)
- [x] **E1** Rule pack (`rules/biasclear-rules.json`) and a zero-dependency Python engine that loads it; parity with v1 on the golden file. Done by the seed commit (see `ops/SEED_NOTES.md` in the seed).
- [ ] **E2** Zero-dependency TypeScript engine (`packages/engine`) that reads the same rule pack, including citation suppression; golden-file parity with Python. **Built, in review.** It follows decision 24: the engine emulates Python's `re`, so browser and Python results are identical, pinned by 27 Unicode golden cases. It opens as a PR after the seed merges and the access test passes. Owner merge, because it adds Node to the CI `test` job.
- [ ] **E3** Symmetry: structural rules replace named-entity lists; fix name-length windows, unmirrored label lists and rule words inside names. Target 120+ swapped pairs (the symmetry script prints the actual count), every rule in at least one pair. Required pairs include listed vs unlisted agency (CDC vs CBO, FBI vs USDA), think tanks of opposite lean (Heritage vs Brookings, Cato vs Center for American Progress) and credentials (Harvard, Yale, Hillsdale, Berkeley). The README's withdrawn example sentences are a permanent regression test. All pairs green in Python and TypeScript. It runs inside the required `test` job, so no new required check.
- [ ] **E4** Benchmark harness on PTC-SemEval20 (Zenodo record 3952415; reported as CC BY 4.0 with no registration, unverified). The fetch script checks the license and checksum and stops on any mismatch. Data is never committed, uploaded as an artifact or printed. The rule-to-technique mapping is committed before the first scored run; published numbers come from a sealed, hash-selected half. Per-rule precision and recall go to `bench/results/`. SemEval-2023 Task 3 is deferred: its data agreement reportedly limits use to the shared task (unverified).
- [x] **E5** Retire the v1 "truth score". Done by design: v2 returns moves and per-tier counts, and has no score.
- [ ] **E6** Neutral rule names and descriptions: describe structure, never intent; before S1 builds the Field Guide from the pack

### 2: Our own labeled set (after launch; PM designs, no paid labelers)
- [ ] **L1** Written labeling guide (what counts as each move, what doesn't), from the PIT preprint's definitions. It never quotes rule-pack trigger phrases, and a red-team pass checks it for leakage before it is hashed. Pre-registered and hashed before any labeling.
- [ ] **L2** Separation of duties: the rules are frozen and hashed *before* labeling. Labels come from a blind labeler job (the Anthropic API from GitHub Actions) that never sees the rules. Refused items are counted, not dropped. An agreement threshold is set before any number is published. Only texts we may republish (otherwise URL, offsets and hash). The owner spot-checks a sample sized to his weekly budget. Guide, labels and hash are all published, marked as secondary evidence. Numbers are tagged "LLM-labeled, owner-audited, secondary, single model family" unless the owner later approves a labeler from a second model family.

### 3: Brand and site (PM designs, Codex builds)
- [x] **B1** Brand direction: Lightbox (PM, delegated by owner)
- [ ] **B2** Design tokens and wordmark (SVG), tier colors, type (self-hosted); contrast script inside `test`
- [ ] **S1** Static site (Home checker, Field Guide, Method, Privacy, About; Developers if time allows) on GitHub Pages in `biasclear/biasclear`, deployed by the Pages workflow. Depends on E6 and B2.
  - Pasted text reaches the page only as text, never as HTML; hostile-string tests cover it.
  - No `http://` links; every URL works at the domain root.
  - Privacy page says only what is true of the deployed site: GitHub, as host, logs visitor IP addresses; BiasClear runs no analytics and sets no cookies; checker text never leaves the tab; mail to hello@ is held by the mailbox provider. The v1 signup note goes in only after the email is sent and the list deleted. Any PR that adds a network request, storage or a new origin updates this page in the same PR.
  - A copy check inside the required `test` job scans user-facing copy (README.md, site pages, the pyproject description) for claim-shaped phrases from the AGENTS.md "Truth in copy" list (for example "truth score", "certified", "compliant", "% recall"). A checked-in allowlist covers the AGENTS.md ban list itself and negations.
  - Automated accessibility check green; one manual screen-reader pass before Gate A. The owner does it in about 10 minutes of his Nov 9 review (VoiceOver on a phone: paste the sample, confirm the count is announced and the list is readable), logged in the time log.
  - The owner reviews the full site privately (a claude.ai artifact preview). On launch day the Pages deploy switches from the placeholder to the site.
- [ ] **S2** Share cards rendered locally (no server), with alt text; poster of the Field Guide as HTML or tagged PDF

### 4: Distribution (after Gate A)
- [ ] **D1** npm first publish, and the first stable PyPI release (2.0.0a1 in Phase 0 is the first release)
- [ ] **D2** MCP server so AI agents can lint their own drafts
- [ ] **D3** Browser extension (after Feb 1, if users show up)

### 5: Lab
- [ ] **F1** Fidelity Trace: compare a source against a retelling and show what was dropped, hardened, unsourced, or had its numbers changed

## Outside signals (for Gate B)

The PM logs each one. The owner has nothing to do here.

| Date | Type (educator, citation, researcher, journalist, stars) | Link | Logged by |
|---|---|---|---|

## Decisions log

| Date | Decision | By |
|---|---|---|
| 2026-09-26 | Relaunch: honest, browser-only, launch week of Nov 16, build starts now | Owner |
| 2026-09-26 | Agents may push branches and open PRs | Owner |
| 2026-09-26 | Labeling is done in-house (no paid labelers) | Owner |
| 2026-09-26 | Owner is not featured on the site; small citation plus a contact address only | Owner |
| 2026-09-26 | Brand design delegated to PM. Direction: **Lightbox** (paper-and-ink page; a loupe reveals persuasion structure as a film negative, colored by PIT tier). Strings dropped: it reads as intent, not structure | Owner → PM |
| 2026-09-26 | New GitHub organization `biasclear`; retire old repos once nothing depends on them | Owner |
| 2026-09-27 | Blueprint revision 2 approved | Owner |
| 2026-09-27 | License: Apache-2.0 for code, CC BY 4.0 for the rule pack; v1 code, including `v1-final`, stays AGPL-3.0 | Owner |
| 2026-09-27 | Signup notice: email the affected signups once, plus a short public note; delete the list after sending | Owner |
| 2026-09-27 | Project mailbox: Namecheap Private Email (Launch plan) for hello@biasclear.com | Owner |
| 2026-09-27 | First PyPI release is a clean v2 alpha, 2.0.0a1 (rules only, zero dependencies), not a v1 re-release; retired v1 code kept as a scrubbed `v1-final` snapshot for the preprint | PM |
| 2026-09-27 | `bws82/biasclear-action` backed up to the private Drive archive, then deleted. Never recreate it as a stub or listing | PM |
| 2026-09-27 | 1. The owner creates the new repo with a README; the PM's seed arrives as a PR on top of it, and the owner merges it | PM |
| 2026-09-27 | 2. Codex starts from one PM comment on the ticket issue (no stub draft PR), with checks at 2 and 60 minutes and a fixed fallback ladder; the 24-hour fallback choice is the owner's | PM |
| 2026-09-27 | 3. The Codex handle appears only in the PM's trigger comments: the one start comment per ticket, plus one new follow-up comment on the PR per round of blocking findings (decision 4). Never anywhere else, and no old comment is edited to add it. This refines the first wording ("only in that one start comment") to match AGENTS.md | PM |
| 2026-09-27 | 4. Follow-ups on a Codex PR: one PR comment first; if the head commit doesn't change, re-trigger on the issue for a replacement PR | PM |
| 2026-09-27 | 5. One GitHub identity, one enforced gate (the `pypi` Approve). No Claude session gets settings or deployment permissions; never connect GitHub through `/web-setup` or a token | PM |
| 2026-09-27 | 6. Red-team verdicts are Comment reviews plus a `redteam:clear` / `redteam:blocking` label; the PM merges an unprotected-path PR only with `redteam:clear` and green checks | PM |
| 2026-09-27 | 7. The PM relies on CI job logs for secret findings | PM |
| 2026-09-27 | 8. Releases stay tag-triggered (`v[0-9]*`) behind the `pypi` environment's owner Approve; the owner creates release tags on the Releases page until the access test shows the PM can | PM |
| 2026-09-27 | 9. PyPI account on hello@, username `biasclear`; first version 2.0.0a1, never 0.x or 1.x; never delete a project, release or file (yank instead) | PM |
| 2026-09-27 | 10. `v1-final` is an orphan commit pushed after the seed merges; tagged by the PM if it can, otherwise by the owner | PM |
| 2026-09-27 | 11. Mailbox: Private Email Launch plan, paid 1 year, auto-renew on; aliases are today's forwards plus `dmarc` | PM |
| 2026-09-27 | 12. Mail DNS: MX and SPF from Mail Settings, DKIM at `privateemail._domainkey`, DMARC starts at `p=none` (see 27) | PM |
| 2026-09-27 | 13. Account recovery design: set out in the owner's private checklist | PM |
| 2026-09-27 | 14. Hosting is GitHub Pages; domain verified at the org level; soft limits 100 GB a month and a 1 GB site | PM |
| 2026-09-27 | 15. biasclear.com shows a one-page placeholder from Render's removal until launch; the owner reviews the full site privately | PM |
| 2026-09-27 | 16. Pages can't send response headers; Mode B hosting is decided before its spec is final | PM |
| 2026-09-27 | 17. The Privacy page says GitHub logs visitor IPs; no analytics before Gate B unless the owner approves a cookieless count | PM |
| 2026-09-27 | 18. Render sitting: fixed order, done with the PM live; one recorded exception to "no terminal" (a single paste); details in the private checklist | PM |
| 2026-09-27 | 19. Signup notice: from hello@ in BCC batches of 50 at most; plain about the v1 privacy page being wrong; says the list is deleted after sending; one line pointing to the public note | PM |
| 2026-09-27 | 20. The owner's personal GitHub account is never renamed or deleted | PM |
| 2026-09-27 | 21. Sittings are 30 minutes or less, web clicks only | PM |
| 2026-09-27 | 22. The Owner Console is the owner's source of truth for his steps | PM |
| 2026-09-27 | 23. Domain auto-renew fires about Jan 19, 2027 (about $15), before Gate B; accepted | PM |
| 2026-09-27 | 24. E2 Unicode: option (a), the TypeScript engine emulates Python's `re`, so browser and Python results are identical | PM |
| 2026-09-27 | 25. The owner's step list and the unsent signup-notice draft stay private; public docs link neither | PM |
| 2026-09-27 | 26. Public docs never call the PyPI name unclaimed; they say the first release claims it | PM |
| 2026-09-27 | 27. DMARC goes `p=none` → `p=quarantine` after 2 to 4 weeks of clean reports; `p=reject` only later, if ever, as the owner's choice. The signup notice waits on the mailbox test, not on DMARC (replaces the `p=reject` parts of 12 and 19) | PM |
| 2026-09-27 | 28. Signup notice by about Oct 26, to everyone on the list, with one sentence on likely consequences; a private dated breach record; the owner decides on a legal consult if the list is large or has many EU/UK addresses | PM |
| 2026-09-27 | 29. PyPI now emails a confirm link for logins from a new device, so the mailbox must work before PyPI; a passkey is recommended as the main second factor, TOTP as backup | PM |

## Owner time log

Budget: at most 2 hours a week, at most 30 minutes per sitting, web clicks and decisions only.

| Date | Task | Estimate | Actual |
|---|---|---|---|
