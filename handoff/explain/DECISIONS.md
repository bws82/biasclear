# Explain (Mode C): what the owner decides

Revision 2, after the red team's first review. Each item says what the choice is, what I recommend, and why, in plain words. The design these feed is `SPEC.md`, next to this file. Nothing is built or switched on until you answer D1, and nothing costs money until you finish the one-time setup in D8.

Reply with the numbers you agree with, for example "D1 to D14 as recommended", or change any of them.

---

**D1. Change the privacy promise so Explain is allowed.**
Today the rules say your visitors' text never leaves their browser, and that a hosted AI mode needs that rule rewritten first. Explain breaks the old promise for one sentence, and only when a visitor asks. These texts change:

- **The agent rulebook (`AGENTS.md`)** gets this line in place of the hosted-AI sentence: *"The one hosted exception is Explain (Mode C): only after the visitor presses Explain on a marked move and agrees, the page sends that one sentence to BiasClear's Explain service, which keeps no copy. It is labeled at the button and on the Privacy page, and it follows `ops/BLUEPRINT.md` §4 and the Explain spec."*
- **The same file** adds three things to the list of files only you merge: the `explain/` folder (the service's code, its instructions to the AI, and its Amazon setup), and the two site files that decide what the page sends (`site/js/explain.js`, `site/data/explain.json`).
- **The blueprint** is updated to match D2 to D4 (§4 currently names Opus 5.5, a $50 Anthropic limit, and "AWS not needed"), and its line about the GitHub-to-Amazon login (§5) is corrected to say what is really built (D8).
- **Later, in the release that switches Explain on:** every public page that says text never leaves the browser changes in the same step. That is the Privacy page, two places on the home page, the README (which you merge) and the security note. Their new wording is in `SPEC.md` §12.

**Recommend: yes.** The checker itself doesn't change, and still sends nothing. You merge these because they're protected files.

---

**D2. Which AI model writes the explanations.**

| Choice | Cost per Explain | Explains per $25 | Notes |
|---|---|---|---|
| **Claude Sonnet 5** | about 0.4 cents | about 6,000 | Current, fast, released June 2026 |
| Claude Haiku 4.5 | about 0.2 cents | about 12,000 | Older and simpler; Anthropic may retire it on its own service from mid-October 2026, and Amazon sets its own date |
| Claude Opus 5.5 | over 0.8 cents | under 3,000 | Its "thinking" can't be switched off, so it's slower and costs more for a two-line answer |

**Recommend: Sonnet 5, and only Sonnet 5.** It's the best balance for short, careful, neutral writing. The service is built for this one model, so there is less to test and less to get wrong. Changing the model later is not one setting: it is a reviewed change to the code and prices, a small update to the setup you create in D8, and one "Hello" to the new model in Amazon's playground.

---

**D3. Where Amazon may process the sentence.**

- **One US region, N. Virginia** (recommended). The sentence is processed in that one region.
- **Anywhere in the world:** about 10% cheaper (about 0.04 cents less per Explain), but the Privacy page could no longer say where.

Amazon also offers a wider "US" routing, but it can send text to Canada as well, and it costs the same as one region. So we don't use it.

**Recommend: one US region.** It costs the same as Amazon's US routing, and the Privacy page can say exactly "in the United States (N. Virginia)". Changing this later is a reviewed change plus an update to the setup.

---

**D4. The monthly spending cap.**
Explain stops calling the AI model for the rest of the month once the model has cost this much, counted at full price, whatever credits you have. It also stops for the rest of the day once it has spent one tenth of the cap, so one busy or abusive day can't use the whole month.

The cap covers the AI model, which is almost all of the cost. The small Amazon services around it (the web address, the function, the counters, the logs) have no hard stop. At normal use they cost under $1 a month. If someone flooded the service at its full speed for a whole month, they could add about $15 to $20. **So the worst month you should plan for is about $45.** The budget emails in D5 would reach you along the way.

**Recommend: $25 a month, with a daily limit of $2.50.** That's about 6,000 explanations a month, about 600 a day. Lowering the cap is one run in GitHub. Raising it above $25 is a small reviewed change plus one number in your setup, done together.

---

**D5. A second, automatic stop from Amazon.**
Amazon's budget tool watches the whole AWS account, ignoring credits and including tax. It emails you when the month reaches half of $30 (the cap plus $5 for small running costs), when it reaches $30, and when Amazon forecasts it will pass $30. The forecast email only starts working after a few weeks, once Amazon has some billing history. At $30 it also switches off Explain's access to the AI model by itself, and Explain stays off until someone checks why and switches it back. Amazon's numbers lag by several hours, so this is a safety net, not the main stop.

It can fire for two reasons: our own counter was wrong, or someone flooded the service and ran up the small charges in D4. Either way, a person should look before Explain comes back.

Because the budget watches the whole account, **use this AWS account for Explain only.**

**Recommend: yes, with emails to hello@biasclear.com.**

---

**D6. Limits per visitor, and one risk to accept.**

**Recommend:**
- 10 explanations per 10 minutes, and 50 per day, from one internet connection.
- 2 per second across everyone.

These keep one person or one script from using up everyone's money. To count per connection, the server stores a scrambled code, never the address itself. The code can't be turned back into the address once the day's secret is thrown away, after about two days.

**The risk:** the 2-per-second limit is shared. One script sending 2 requests a second can fill it, and while it does, every other visitor sees "Explain is busy". Amazon's per-visitor shield for this can't be used with this kind of service. The checker keeps working, because it never needs Explain.

**Recommend: accept this risk.** If it ever happens, you can pause Explain (D8) until it stops.

---

**D7. When to switch it on for visitors.**

**Recommend:**
1. Build it now.
2. Test it live with made-up sentences, with the red team reading every answer side by side. Each test sentence is asked five times, because the AI's wording varies a little each time.
3. Switch the button on only **after** the public launch (week of November 16) and after you say yes.

Explain is not part of the launch floor. The checker, Field Guide, Method, Privacy and About don't need it. Switching it on or off for visitors is one reviewed change in the repository, which you merge.

---

**D8. The one-time setup, how you deploy, and what your approval really does.**

The one-time setup is one sitting of about 25 minutes, clicks only:
- check the credit;
- send one "Hello" to the model in Amazon's playground;
- confirm a logging switch is off, and set Amazon's data-keeping setting (D13);
- upload one setup file to Amazon;
- create one GitHub "environment" with you as the approver;
- run the first deploy;
- press Amazon's emergency stop once and undo it, so you know it works.

A true one-click link isn't possible for the very first step: Amazon requires the file to be stored in Amazon first, and your account has nothing there yet.

After that, **deploying, pausing and resuming are each two clicks in GitHub:**
1. **Run workflow** (choose deploy, pause or resume)
2. **Approve and deploy**

Pausing changes only the on/off switch. It doesn't rebuild or ship anything new, so it works even when other work is half done. Nothing runs by itself: a change merged into the repository waits until you run a deploy. Changing the model, the region, or raising the cap above $25 is a reviewed change plus a small update to your setup, not a setting.

No key or password is ever shown, copied or stored. GitHub proves who it is to Amazon each time, and only for runs you approve, from the main branch.

**What your approval does and doesn't do, plainly.** Some fences are locks. Amazon itself stops the service from touching any other model, any other data, or its own permissions, whatever its code says. One fence is a promise. Every agent works through your GitHub account, so GitHub can't tell your clicks from theirs. If an agent started a run and you approved it without noticing, code you didn't mean to ship could go live, and that code could mishandle visitors' sentences. The red team reads every change, and you merge every change to the Explain files, but you can't be expected to read code. So there is one rule, and it is the whole of your job here:

> **Approve only a run you started yourself, just now.** If GitHub emails you about a run waiting for approval that you didn't start, don't approve it. Tell the PM.

Each run's page shows, in plain words, what it will do and what changed since the last deploy, above the approve button.

**Recommend: yes.** The PM prepares the setup file with the project's public GitHub numbers already filled in, so the only things you type are the setup's name (`biasclear-explain-setup`) and your 12-digit AWS account number.

---

**D9. Which AWS sign-in you use for the one-time setup.**

**Recommend: your main (root) sign-in, with two-factor on, for the setup sitting only.** After that you only need to sign in to AWS for the emergency stop, or to read the bill.

AWS advises against using the root sign-in for daily work. Making a separate admin identity first would add about 15 minutes of clicks.

---

**D10. The web address of the Explain service.**

- **Amazon's default address** (a long `…execute-api.us-east-1.amazonaws.com` name): works now, no extra steps.
- **A `biasclear.com` address** (for example `explain.biasclear.com`): needs a certificate and a DNS record at Namecheap. That's about 10 minutes of your clicks, plus waiting.

**Recommend: Amazon's default address at first.** It's shown only in the checker page's security policy and on the Privacy page. Move to a biasclear.com address later if you like.

---

**D11. The AWS credit.**
Claude on Amazon is billed as "AWS Marketplace" usage. Most AWS credits don't cover Marketplace. AWS's Activate terms make one exception, for AI models on Amazon Bedrock. I could read that exception only through search results, not the page itself.

**Recommend:**
1. In the setup sitting, open **Billing → Credits** and send the PM a screenshot of the credit's name, expiry date and "applicable products", so we know it really covers Bedrock.
2. The PM adds a reminder one month before the credit expires.

When the credit runs out, Explain keeps working and charges real money, never more than the cap for the model (D4).

---

**D12. The old Render account.**
The blueprint kept Render "for a possible hosted AI mode". Explain uses AWS instead.

**Recommend: close the Render account** after the planned v1 cleanup, as one fewer account to secure. Low priority, and your call.

---

**D13. Amazon's data-keeping setting for this account.**
Amazon's AI service has one account-wide setting that decides what happens to the text it is sent. The choices include "keep nothing" (zero data retention), Amazon's standard handling, and modes where Amazon may review the text or share it with the AI model's maker. Some newer AI models on Amazon only work in the sharing mode. If anyone switched this account to that mode, for example to try one of those models, Explain's sentences would be covered by it, and our Privacy page would be wrong.

**Recommend:**
1. In the setup sitting, set it to **keep nothing** (zero data retention). The first deploy's test proves Sonnet 5 answers under it. If Sonnet 5 won't, set it to Amazon's **standard** handling instead, and the Privacy page says what that means (Amazon may keep requests for abuse checks for up to 30 days, if its page lists this model).
2. Explain checks this setting, and the logging switch, by itself every 15 minutes, and pauses if either has changed.
3. **Never change this setting in this account**, and never switch on data sharing. If you want to try other AI models, use a separate AWS account.

---

**D14. The "plainer way to say it" line.**
Each answer has two parts: how the wording works, and the same sentence written more plainly. The second part is harder to get right. A good rewrite keeps who is speaking and how sure the sentence sounds, and changes only the marked words. A bad one could quietly make the claim weaker or stronger, and it would appear on our page.

**Recommend:** the live test (D7) checks every rewrite for exactly that. If fewer than 9 in 10 pass, the first version ships with the "how the wording works" part only, and the rewrite comes back once it passes. Either way, the page shows the rewrite in quotation marks, as a rewrite of the visitor's own sentence, never as BiasClear's own words.
