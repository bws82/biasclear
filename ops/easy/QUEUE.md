# BiasClear easy-button queue

The PM (a cloud Claude session) prepares each item. The BiasClear "hands" thread on the owner's Mac runs them one at a time, only when the owner presses run. Each command is pinned to an exact file version and checks the file's fingerprint before it runs.

Status values: `ready` (run it next), `done`, `hold` (don't run).

## 1. Repository settings, in the browser — done (2026-09-28), except step 4

Result: steps 1, 2 done; steps 3, 5, 6 were already set. Step 4 (the pypi approval rule) was blocked by the browser helper's permission layer; the environment exists with no rules. It moves to the release sitting.

What it does, in one line: sets the new repository's settings on GitHub's website, in the owner's own Chrome (description and topics, tidy defaults, read-only checks, the release approval switch, the free security scanners).

How: use Claude in Chrome in the owner's own Chrome, where he is signed in to GitHub. Follow these steps exactly and change nothing else. Never type a password, code or key. If GitHub asks the owner to confirm it's him (passkey, security key or code), stop and tell him to do it, then carry on. If a page looks different from these steps, or a control is greyed out, don't guess: note it and move to the next step.

1. Open https://github.com/biasclear/biasclear . On the right, next to "About", press the gear icon.
   - Description: `Marks the persuasion moves in any text, in your browser. Same rules for everyone, tested in public.`
   - Leave Website empty.
   - Topics, one at a time: `persuasion`, `rhetoric`, `media-literacy`, `critical-thinking`, `bias-detection`, `open-source`, `python`, `typescript`.
   - Press "Save changes".
2. Open https://github.com/biasclear/biasclear/settings . Under "Features", untick "Wikis" and untick "Projects". Under "Pull Requests", tick "Automatically delete head branches". Leave "Allow auto-merge" unticked. (Each change saves by itself.)
3. Open https://github.com/biasclear/biasclear/settings/actions . Under "Workflow permissions", choose "Read repository contents and packages permissions", untick "Allow GitHub Actions to create and approve pull requests", and press Save. If this section is greyed out, open https://github.com/organizations/biasclear/settings/actions and make the same two changes there, then Save.
4. Open https://github.com/biasclear/biasclear/settings/environments and press "New environment". Name: `pypi`. Press "Configure environment". Then:
   - Tick "Required reviewers" and add `bws82`.
   - Leave "Prevent self-review" unticked.
   - Untick "Allow administrators to bypass configured protection rules" if it's there.
   - Under "Deployment branches and tags", choose "Selected branches and tags", press "Add deployment branch or tag rule", set "Ref type" to Tag, type `v*`, and press "Add rule".
   - Press "Save protection rules".
   If a `pypi` environment already exists, open it and check these settings instead of making a second one.
5. Open https://github.com/biasclear/biasclear/settings/security_analysis . Press Enable (or turn on) for each of these that is off: "Private vulnerability reporting", "Dependabot alerts", "Secret scanning" (or "Secret Protection") and "Push protection". Leave everything else as it is, and don't start any paid trial.
6. Open https://github.com/biasclear/biasclear/settings/pages and check that "Source" says "GitHub Actions". Don't type anything under "Custom domain".

Done when: each of the six steps is done or clearly reported. Report back in one short list, one line per step: done, already set, or what was different.

## 1-alt. The same settings by command — hold

Only if the owner asks for the command route instead of the browser. It needs his real GitHub sign-in, so it must run in his Mac's own Terminal, never in a sandbox.

What it does, in one line: sets the new repository's settings through GitHub's own tool, signed in as the owner (read-only checks, the release approval switch, the free security scanners, the website source, the description and topics).

Also, on purpose: hides the unused Wiki and Projects tabs, deletes a work branch automatically after it's merged (restorable), and saves its output to biasclear-easy-button.txt on the Desktop.

Where to run: it needs the owner's real GitHub sign-in, so it must run in his Mac's own Terminal, never in a sandbox. Show the command in a code box so he can press its ▷ run button, then wait for him to say "pressed".

Needs: GitHub's command-line tool `gh`. If it isn't installed, install it first with `brew install gh` if Homebrew is present; otherwise tell the owner to get the macOS installer from https://cli.github.com and stop. If `gh` asks to sign in, run `gh auth login --hostname github.com --git-protocol https --web` in an interactive terminal and walk the owner through it (copy the code, press Return, paste it in the browser, touch the key).

Command:

```
curl -fsSL https://raw.githubusercontent.com/bws82/biasclear/899c3fc453dcbdac2309c7c05cb9b0737c88011e/ops/easy/github-settings.sh -o /tmp/bc-settings.sh && echo "f89f7b829b93fc690a2fc3530e2e9b6e6002d1bcb70f926f50e2bff6c204ca75  /tmp/bc-settings.sh" | shasum -a 256 -c && bash /tmp/bc-settings.sh
```

Done when: it prints "Finished: 9 done, 0 not done". Show the owner the "Report for your PM" lines.

## 2. Two web-only settings — hold (moves to the mailbox run)

The browser helper's permission layer blocks org admin changes and Namecheap. Steps 1 to 3 and 5 go into the mailbox run; step 4 (require 2FA) is the owner's own tick.

What it does: locks biasclear.com to the GitHub organization (adds one TXT record at Namecheap) and turns on the organization's two safety switches. GitHub only allows these on its website.

How: use Claude in Chrome in the owner's own Chrome, where he is signed in to GitHub and Namecheap. Follow these steps exactly. Never type a password, code or key; stop when a site asks the owner to confirm it's him. Change nothing else.

1. Open https://github.com/organizations/biasclear/settings/pages . Under "Verified domains", press "Add a domain", type biasclear.com, press "Add domain". Note the TXT host and value it shows.
2. Open https://ap.www.namecheap.com/domains/list/ , press Manage next to biasclear.com, open Advanced DNS, press "Add New Record". Type: TXT Record. Host: _github-pages-challenge-biasclear . Value: the value from GitHub. TTL: Automatic. Press the green check. Don't change or delete any other record.
3. Back on GitHub, press Verify. If it can't verify yet, report "domain: pending" (DNS can take up to an hour).
4. Open https://github.com/organizations/biasclear/settings/security . Tick "Require two-factor authentication for everyone in the biasclear organization" and save.
5. Open the organization's Settings, then Moderation, then "Code review limits". Press "Limit review on all repositories" if offered.

Done when: each of the five steps is done or clearly reported.

## 3. Protect main (the "protect-main" ruleset) — ready, once the seed's checks have passed on main

What it does, in one line: makes main changeable only through a pull request whose four checks (test, security, secret-scan, sast) have passed, with no force pushes, no deletion and nobody able to bypass it; then reads every field back from GitHub.

It checks first that the four checks passed on the newest commit on main. If they haven't yet, it says "not yet" and changes nothing; press it again later. It's safe to press twice (the second time it just confirms). Its output is also saved on the Desktop as biasclear-protect-main.txt.

Where to run: it needs the owner's real GitHub sign-in, so it runs in his Mac's own Terminal, never in a sandbox. Show the command in a code box so he can press its ▷ run button, then wait for him to say "pressed".

Command:

```
curl -fsSL https://raw.githubusercontent.com/bws82/biasclear/0b78222b12a6a383a18d993548b19e8bf629fe68/ops/easy/protect-main.sh -o /tmp/bc-protect-main.sh && echo "9b4d4a12dc0558a4c7cc452e0b955beae506e0bcf30e9df7cdb87223e9dfe085  /tmp/bc-protect-main.sh" | shasum -a 256 -c && bash /tmp/bc-protect-main.sh
```

Done when: the report says "12 checks passed, 0 failed". Show the owner the "Report for your PM" lines; the PM confirms the read-back.

## 4. HTTPS for biasclear.com, and the Pages checks — ready, after biasclear.com points at GitHub Pages

What it does, in one line: turns on "Enforce HTTPS" once GitHub has issued the certificate for biasclear.com, checks that only main can publish the site (adding that rule if there is none), and, once https://biasclear.com/ serves the site, sets the repository's Website link to it.

Anything not ready yet is reported as "not yet" and left unchanged; press it again in an hour. It never removes a setting. Its output is also saved on the Desktop as biasclear-pages-https.txt.

Where to run: same as item 3 (his Mac's own Terminal, ▷ then "pressed").

Command:

```
curl -fsSL https://raw.githubusercontent.com/bws82/biasclear/0b78222b12a6a383a18d993548b19e8bf629fe68/ops/easy/pages-https.sh -o /tmp/bc-pages-https.sh && echo "64934e512f85876e2437b9bbd3767cc6bb0aea69a99d1c1aafb25280ab52c91a  /tmp/bc-pages-https.sh" | shasum -a 256 -c && bash /tmp/bc-pages-https.sh
```

Done when: the report says "3 done, 0 not yet, 0 need your PM". Show the owner the "Report for your PM" lines.
