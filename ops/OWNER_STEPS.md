# Owner steps

The only tasks that need the owner's own hands. **Web clicks and decisions only**: no terminal, and no sitting over 30 minutes. Do them in order; each says what it unblocks. Tell the PM "sitting N done", or send a screenshot of anything that looks different from these steps.

Never paste a password, key, code or card number into chat. If a step shows one, it stays on that page.

**You pay and you approve; agents build.** Any helper agent, including a browser agent, prepares everything up to a payment, a terms acceptance, an approval or a delete, and then stops for you.

---

## Sitting 1: safety first (15 min). Safe to do now.

**1a. Namecheap two-factor.** namecheap.com → your name (top right) → **Profile → Security → Two-Factor Authentication** → choose **TOTP (authenticator app)**, not SMS. Scan the QR code, enter the 6-digit code, and save the backup codes offline.

**1b. Namecheap auto-renew on.** **Domain List → biasclear.com**. Turn **Auto-Renew** on for the domain and its privacy protection. Project accounts will recover through this domain, so it must not lapse by accident. (This reverses the earlier "leave it off" advice.)

**1c. GitHub email privacy.** github.com → **Settings → Emails**. Tick **Keep my email addresses private** and **Block command line pushes that expose my email**.

**1d. Delete the old GitHub Action.** github.com/bws82/biasclear-action → **Settings** → scroll to **Danger Zone → Delete this repository** → type the name to confirm.
- Why: it tells anyone who uses it to `pip install biasclear`, and that name is currently unclaimed, so a stranger could publish code under it.
- The PM confirmed nothing depends on it.

*Unblocks:* safe accounts and closing the package-name hole.

---

## Sitting 2: the new home (10 min)

**2a.** Open github.com/biasclear. If it shows a page, the name is taken; stop and tell the PM.

**2b.** Create the organization: github.com → **+** (top right) → **New organization** → **Free** → name `biasclear`. For the contact email, use one you're comfortable GitHub seeing; it isn't shown publicly.

**2c.** Install the agents on it:
- **Claude:** go to claude.ai/connect-github, install the Claude GitHub App on the `biasclear` organization, and choose **All repositories**.
- **Codex:** in ChatGPT → Codex → Settings → GitHub, install the Codex connector on the `biasclear` organization.

*Unblocks:* the PM seeds the clean repo and claims the PyPI name.

---

## Sitting 3: decisions ✅ done 2026-09-27

Blueprint approved; Apache-2.0 plus CC BY 4.0; email the signups plus a public note; Namecheap Private Email for hello@.

---

## Sitting 4: project mailbox (20 min)

Namecheap Private Email **Launch** plan (called Starter on older pages): one mailbox, about $15 a year, with a 30-day free trial.

1. namecheap.com → **Email → Private Email** → **Get Launch** → **Use a domain I own with Namecheap** → **biasclear.com** → checkout. You enter the payment yourself.
2. **Before switching mail over**, write down every address that forwards today. Namecheap → **Domain List → biasclear.com → Manage → Redirect Email** lists them (for example `brad@`).
3. In the Private Email setup, create the mailbox **hello@biasclear.com** with a new strong password (store it in your password manager). Display name: **BiasClear**. Then add each address from step 2 as an **alias** of this mailbox, so nothing that arrives today gets lost.
4. Namecheap → **Domain List → biasclear.com → Advanced DNS → Mail Settings** → choose **Private Email**. Namecheap adds the mail records (MX and SPF) for you.
5. In the Private Email admin, turn on **DKIM** for the domain and follow its prompt to add the DKIM record. Tell the PM when it shows as active.
6. Tell the PM "mailbox up". The PM gives you one DMARC line to add as a TXT record, then asks you to send a test mail to and from hello@.

From then on, you answer anything BiasClear-related from hello@biasclear.com, never from your personal inbox.

*Unblocks:* PyPI account, signup notice.

---

## Sitting 5: PyPI (10 min, after sitting 4 and the new repo exist)

1. pypi.org → **Register**. Use `hello@biasclear.com` and a username with no personal name in it (for example `biasclear`). Verify the email.
2. **Account settings → Two factor authentication → Add TOTP application.**
3. **Publishing → Add a new pending publisher.** Paste the four fields the PM gives you (they name the `biasclear/biasclear` repo). Then tell the PM.
4. The PM runs the release right away. **The name is only claimed once that first release publishes.** A pending publisher on its own doesn't reserve it.

*Unblocks:* nobody else can publish `biasclear`.

---

## Sitting 6: Render and DNS cleanup (30 min, with the PM live; needs decision 3)

The live v1 service is called **`biasclear`**. It holds the domain, the old keys and the signup list. `biasclear-api` is an older leftover. **Both go.**

1. dashboard.render.com: tell the PM every service name you see, and whether any **Environment Groups** exist.
2. If decision 3 includes emailing signups, the PM walks you through exporting the list first. It changes a setting so the old app can't show anything, then runs one paste-in command. **Don't delete anything until the PM says the export is done.**
3. On the `biasclear` service: **Settings → Custom Domains**, remove `biasclear.com` and `www.biasclear.com`.
4. **Same sitting**, in Namecheap → **Domain List → biasclear.com → Advanced DNS**: delete the **A record** for `@` (216.24.57.1) and the **CNAME** for `www` (biasclear.onrender.com). **Don't touch mail records.** Leaving these pointing at Render would let someone else claim the domain there.
5. Delete both services: each service → **Settings** → bottom → **Delete Web Service**. Their disks go with them. Delete any Environment Groups too.
6. **Keep the account.** Under **Billing**, tell the PM the plan name, whether a card is on file, and the credit balance, **expiry date** and where it came from.
7. Turn on Render two-factor: **Account Settings → Security**.

*Unblocks:* the old key and stored credentials are gone; the domain is safe for the new site.

---

## Sitting 7: protect the new repo (5 min, when the PM says CI has run once there)

github.com/biasclear/biasclear → **Settings → Rules → Rulesets → New branch ruleset** → target `main`:
- **Require a pull request**, with **Required approvals: 0** and **Require review from Code Owners: off** (all agents act as your account, so GitHub can't enforce owner review).
- **Require status checks to pass:** `test`, `security`, `secret-scan`, `sast`.
- **Block force pushes** and **Restrict deletions**.
- **Bypass list: empty.**

---

## Sitting 8: retire the old repo (15 min, only after the PM confirms the access test passed)

1. The PM puts an archive of the old repo in your private Drive folder `BiasClear Archive`. Check it's there.
2. On zenodo.org, open your PIT record → **Edit** → add a **related identifier** pointing to `https://github.com/biasclear/biasclear` → Save. This is a metadata edit only: don't create a new version.
3. github.com/bws82/biasclear: confirm **Forks: 0**, then **Settings → Delete this repository**.
4. Right away create a new public repo named `biasclear` under your account with a README only. The PM gives you the exact text ("BiasClear moved to …"). Then **Settings → Archive**.
5. Update your profile README link to the new organization.
6. Add a dated note at the top of the EA Forum post: the v1 accuracy, neutrality and compliance claims are withdrawn, with a link to the new repo.

---

## Optional, any time: AWS (10 min, reading only)

**Don't add a card.** Sign in as root → **Billing and Cost Management**:
- **Payments / Bills:** note any unpaid total, and whether the lines say AWS Marketplace, Anthropic or Bedrock.
- **Credits:** for each credit, note its type, remaining balance, expiry, and whether "AWS Marketplace" or "third-party models on Bedrock" appear under applicable products.

Tell the PM the numbers only. The plan doesn't depend on AWS, and the PM will say whether it's worth reactivating or closing.

---

## After launch (not now)

- Anthropic Console account for the AI modes
- npm
- Jarvis gate reviews
