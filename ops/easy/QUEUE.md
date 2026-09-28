# BiasClear easy-button queue

The PM (a cloud Claude session) prepares each item. The BiasClear "hands" thread on the owner's Mac runs them one at a time, only when the owner presses run. Each command is pinned to an exact file version and checks the file's fingerprint before it runs.

Status values: `ready` (run it next), `done`, `hold` (don't run).

## 1. Repository settings — ready

What it does, in one line: sets the new repository's settings through GitHub's own tool, signed in as the owner (read-only checks, the release approval switch, the free security scanners, the website source, the description and topics).

Also, on purpose: hides the unused Wiki and Projects tabs, deletes a work branch automatically after it's merged (restorable), and saves its output to biasclear-easy-button.txt on the Desktop.

Where to run: it needs the owner's real GitHub sign-in, so it must run in his Mac's own Terminal, never in a sandbox. Show the command in a code box so he can press its ▷ run button, then wait for him to say "pressed".

Needs: GitHub's command-line tool `gh`. If it isn't installed, install it first with `brew install gh` if Homebrew is present; otherwise tell the owner to get the macOS installer from https://cli.github.com and stop. If `gh` asks to sign in, run `gh auth login --hostname github.com --git-protocol https --web` in an interactive terminal and walk the owner through it (copy the code, press Return, paste it in the browser, touch the key).

Command:

```
curl -fsSL https://raw.githubusercontent.com/bws82/biasclear/899c3fc453dcbdac2309c7c05cb9b0737c88011e/ops/easy/github-settings.sh -o /tmp/bc-settings.sh && echo "f89f7b829b93fc690a2fc3530e2e9b6e6002d1bcb70f926f50e2bff6c204ca75  /tmp/bc-settings.sh" | shasum -a 256 -c && bash /tmp/bc-settings.sh
```

Done when: it prints "Finished: 9 done, 0 not done". Show the owner the "Report for your PM" lines.

## 2. Two web-only settings — ready (browser)

What it does: locks biasclear.com to the GitHub organization (adds one TXT record at Namecheap) and turns on the organization's two safety switches. GitHub only allows these on its website.

How: use Claude in Chrome in the owner's own Chrome, where he is signed in to GitHub and Namecheap. Follow these steps exactly. Never type a password, code or key; stop when a site asks the owner to confirm it's him. Change nothing else.

1. Open https://github.com/organizations/biasclear/settings/pages . Under "Verified domains", press "Add a domain", type biasclear.com, press "Add domain". Note the TXT host and value it shows.
2. Open https://ap.www.namecheap.com/domains/list/ , press Manage next to biasclear.com, open Advanced DNS, press "Add New Record". Type: TXT Record. Host: _github-pages-challenge-biasclear . Value: the value from GitHub. TTL: Automatic. Press the green check. Don't change or delete any other record.
3. Back on GitHub, press Verify. If it can't verify yet, report "domain: pending" (DNS can take up to an hour).
4. Open https://github.com/organizations/biasclear/settings/security . Tick "Require two-factor authentication for everyone in the biasclear organization" and save.
5. Open the organization's Settings, then Moderation, then "Code review limits". Press "Limit review on all repositories" if offered.

Done when: each of the five steps is done or clearly reported.
