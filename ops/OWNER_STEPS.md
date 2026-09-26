# Owner steps

These are the only tasks that need the owner's own hands, because they involve account security or logins agents shouldn't hold. Each takes under 10 minutes. Tick them off here or just tell the PM "done".

## 1. Namecheap: turn on two-factor (5 min)
1. Log in at namecheap.com, open your name (top right), then **Profile > Security**.
2. Under **Two-Factor Authentication**, pick **TOTP (authenticator app)**, not SMS.
3. Scan the QR code with your authenticator app, then type in the 6-digit code.
4. Save the backup codes somewhere offline.

Leave auto-renew **off** until the February 1 decision.

## 2. Render: shut down v1 for good (5 min)
The old server is suspended. An old API key for it is visible in public git history, and its disk holds the beta-signup list. Signups stored before the March 20 fix were also readable without any key through v1's public `/audit` endpoint until the suspension. Deleting the service kills the key and the data together.
1. Go to dashboard.render.com and open **biasclear-api**.
2. Decide whether you want the beta-signup list. If yes, **stop here and tell the PM**, and we'll export it safely together first.
3. Go to **Settings**, scroll to the bottom, and click **Delete Web Service**. Confirm. This also deletes the 1 GB disk.
4. **Delete only the service, never the account.** The Render account and its credit (about $500) stay for later use.
5. Tidy the account: **Account Settings > Security**, turn on two-factor (authenticator app). Under **Workspace settings**, rename the workspace to `BiasClear`. Under **Billing**, confirm the credit balance and its expiration date, and tell the PM.

## 3. Kill the old cloud keys (5 min)
v2 doesn't need any server-side AI keys.
1. **Gemini:** done (key deleted).
2. **AWS:** the account needs a card to reactivate. Do these in order, and don't add the card first:
   1. Sign in, open **Billing and Cost Management > Credits**, and note the balance, the **expiration date**, and which services the credits cover. Check specifically for Amazon Bedrock.
   2. If the credits are gone, expired, or don't cover Bedrock, stop here. v2 doesn't need AWS.
   3. If they're live, add the card, then right away open **IAM > Users > (the BiasClear user) > Security credentials**. Deactivate the old access key, then delete it.
   4. Open **Billing > Budgets** and create a $5 monthly cost budget with an email alert. It's a tripwire in case anything ever bills past the credits.

## 4. GitHub privacy settings (3 min)
1. Go to github.com, **Settings > Emails**.
2. Tick **Keep my email addresses private** and **Block command line pushes that expose my email**.

## 5. Protect `main` (3 min, before any agent merges)
1. Go to github.com/bws82/biasclear, then **Settings > Branches** (or **Rules > Rulesets**), and add a rule for `main`.
2. Turn on **Require a pull request before merging** and **Require review from Code Owners**.
3. Turn on **Require status checks to pass** and pick `test`, `security`, `secret-scan` and `sast`.
4. Leave force pushes and deletions **blocked**.

## 6. Contact address (2 min)
In Namecheap, open **Domain List > biasclear.com > Manage > Redirect Email** and add an alias `hello` that forwards to your inbox. The site and repo use `hello@biasclear.com` as the only public contact.

## 7. PyPI account (10 min, after step 6 works)
1. Go to pypi.org, click **Register**, and use `hello@biasclear.com` with username `biasclear`. If that's taken, pick something with no personal name in it.
2. Verify the email. Then **Account settings > Two factor authentication > Add TOTP application**.
3. Tell the PM "PyPI ready". The PM then gives you four fields to paste into **Publishing > Add a new pending publisher**. That reserves the name `biasclear` with no password or token ever stored.

## 8. Decision only, no clicks yet: a clean home for v2
Tell the PM which option you want. The PM will write the exact steps.
- **A (PM's pick):** Create a free GitHub organization named `biasclear` and start v2 there as a fresh repo with clean history (no personal email in any commit, no old key). Point PIT v2 (same Zenodo concept DOI) at the new repo first, then archive the old repo as **public** read-only, because the published preprint links to it under Data Availability.
- **B:** Transfer this repo to the `biasclear` org as it is. Old links redirect, but the old history, including the personal email in commits, comes along.
- **C:** Stay under the personal account.
