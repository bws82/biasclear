# Owner steps

These are the only tasks that need the owner's own hands, because they involve account security or logins agents shouldn't hold. Each takes under 10 minutes. Tick them off here or just tell the PM "done".

## 1. Namecheap: turn on two-factor (5 min)
1. Log in at namecheap.com, open your name (top right), then **Profile > Security**.
2. Under **Two-Factor Authentication**, pick **TOTP (authenticator app)**, not SMS.
3. Scan the QR code with your authenticator app, then type in the 6-digit code.
4. Save the backup codes somewhere offline.

Leave auto-renew **off** until the February 1 decision.

## 2. Render: shut down v1 for good (5 min)
The old server is suspended. An old API key for it is visible in public git history, and its disk holds the beta-signup list. Deleting the service kills the key and the data together.
1. Go to dashboard.render.com and open **biasclear-api**.
2. Decide whether you want the beta-signup list. If yes, **stop here and tell the PM**, and we'll export it safely together first.
3. Go to **Settings**, scroll to the bottom, and click **Delete Web Service**. Confirm. This also deletes the 1 GB disk.
4. Your credits stay on the account for later use.

## 3. Kill the old cloud keys (5 min)
v2 doesn't need any server-side AI keys.
1. **AWS:** console.aws.amazon.com, then **IAM > Users**, then the user BiasClear used, then **Security credentials**. Deactivate the access key, then delete it.
2. **Gemini:** aistudio.google.com, then **Get API key**. Delete the key used for BiasClear.

## 4. GitHub privacy settings (3 min)
1. Go to github.com, **Settings > Emails**.
2. Tick **Keep my email addresses private** and **Block command line pushes that expose my email**.

## 5. Decision only, no clicks yet: a clean home for v2
Tell the PM which option you want. The PM will write the exact steps.
- **A (PM's pick):** Create a free GitHub organization named `biasclear` and start v2 there as a fresh repo with clean history (no personal email in any commit, no old key). Archive the old repo as private.
- **B:** Transfer this repo to the `biasclear` org as it is. Old links redirect, but the old history, including the personal email in commits, comes along.
- **C:** Stay under the personal account.
