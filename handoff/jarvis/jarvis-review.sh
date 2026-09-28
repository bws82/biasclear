#!/usr/bin/env bash
# BiasClear easy button: hand the preview to Jarvis for an independent review.
#
# Run it on your own Mac. It does four things, and nothing else:
#   1. Downloads the public BiasClear repository at the exact commit under
#      review into the Claude-Jarvis shared folder (team-board/evidence/).
#   2. Puts the PM's brief in that folder under the next free number.
#   3. Adds one line to CHANNEL-claude-jarvis.md.
#   4. Wakes Jarvis in locked mode with the folder's own wake-jarvis.sh
#      (no internet, no apps, writes only inside the folder).
# It never reads, prints or stores a password, token or key.
#
# Written for macOS's built-in bash 3.2.

set -u

LOG="$HOME/Desktop/biasclear-jarvis-handoff.txt"
[ -d "$HOME/Desktop" ] || LOG="$HOME/biasclear-jarvis-handoff.txt"
exec > >(tee "$LOG") 2>&1
printf 'Saved to %s\n' "$LOG"

REPO_URL="https://github.com/biasclear/biasclear.git"
PR_BRANCH="__PR_BRANCH__"
PR_COMMIT="__PR_COMMIT__"
PR_NUMBER="__PR_NUMBER__"
BRIEF_URL="__BRIEF_URL__"
BRIEF_SHA256="__BRIEF_SHA256__"
TOPIC="biasclear-preview"

stop() { printf '\nSTOPPED: %s\nNothing else was changed. Tell your PM what this says.\n' "$*"; exit 1; }

# 1. Find the shared folder: the one folder under Documents that holds wake-jarvis.sh.
F=""; n=0
for w in "$HOME"/Documents/*/claude-nathan-*/team-board/wake-jarvis.sh; do
  [ -f "$w" ] || continue
  F="${w%/team-board/wake-jarvis.sh}"; n=$((n+1))
done
[ "$n" -eq 1 ] || stop "expected one Claude-Jarvis shared folder with team-board/wake-jarvis.sh, found $n."
printf 'Shared folder found.\n'
command -v git >/dev/null 2>&1 || stop "git is not installed (run: xcode-select --install)."

# 2. Next free brief number: one more than the highest NNN- file in the folder.
max=0
for f in "$F"/[0-9][0-9][0-9]-*; do
  [ -e "$f" ] || continue
  b="${f##*/}"; num=$((10#${b%%-*}))
  [ "$num" -gt "$max" ] && max=$num
done
NNN=$(printf '%03d' $((max+1))); ANS=$(printf '%03d' $((max+2)))
BRIEF="$NNN-claude-to-jarvis-$TOPIC.md"
ANSWER="$ANS-jarvis-$TOPIC.md"
[ -e "$F/$BRIEF" ] && stop "$BRIEF already exists."

# 3. The evidence: the public repository at the exact commit.
SHORT="${PR_COMMIT:0:12}"
EV="team-board/evidence/$TOPIC-$SHORT"
mkdir -p "$F/$EV" || stop "could not create $EV."
if [ ! -d "$F/$EV/repo/.git" ]; then
  git clone --quiet "$REPO_URL" "$F/$EV/repo" || stop "could not download the repository."
fi
git -C "$F/$EV/repo" fetch --quiet origin "$PR_BRANCH" main || stop "could not fetch the pull request branch."
git -C "$F/$EV/repo" -c advice.detachedHead=false checkout --quiet "$PR_COMMIT" || stop "commit $PR_COMMIT is not on the branch."
[ "$(git -C "$F/$EV/repo" rev-parse HEAD)" = "$PR_COMMIT" ] || stop "the checked-out commit is not the one under review."
git -C "$F/$EV/repo" diff --stat origin/main "$PR_COMMIT" > "$F/$EV/diffstat.txt"
printf 'Repository saved at commit %s.\n' "$SHORT"

# 4. The brief, pinned by fingerprint, with this run's names filled in.
tmp="$F/$EV/brief-template.md"
curl -fsSL "$BRIEF_URL" -o "$tmp" || stop "could not download the brief."
echo "$BRIEF_SHA256  $tmp" | shasum -a 256 -c >/dev/null 2>&1 || stop "the brief's fingerprint does not match."
NOW=$(date '+%Y-%m-%d %H:%M %Z')
sed -e "s|__NOW__|$NOW|g" -e "s|__EVID__|$EV|g" -e "s|__ANSWER__|$ANSWER|g" \
    -e "s|__COMMIT__|$PR_COMMIT|g" -e "s|__PR__|$PR_NUMBER|g" "$tmp" > "$F/$BRIEF"
printf 'Brief written: %s\n' "$BRIEF"

printf -- '- **(%s system clock) Claude (BiasClear PM, via the Hands thread):** brief %s (BiasClear preview review → %s) is being answered by a locked wake. Heartbeat Jarvis: please don'"'"'t take %s.\n' \
  "$(date '+%H:%M')" "$NNN" "$ANS" "$NNN" >> "$F/CHANNEL-claude-jarvis.md"

# 5. Wake Jarvis, locked, with the folder's own script. This takes a while.
printf '\nWaking Jarvis (locked). This can take 10 to 40 minutes...\n'
zsh "$F/team-board/wake-jarvis.sh" "$BRIEF" "$ANSWER"
rc=$?

printf '\nReport for your PM\n  brief: %s\n  answer: %s\n  wake exit: %s\n' "$BRIEF" "$ANSWER" "$rc"
if [ -f "$F/$ANSWER" ]; then
  printf '  first line: %s\n' "$(head -1 "$F/$ANSWER")"
  grep -m1 -E 'NO-GO|GO' "$F/$ANSWER" | cut -c1-200 | sed 's/^/  verdict line: /'
else
  printf '  no answer file yet\n'
fi
