#!/usr/bin/env bash
# BiasClear easy button: the "protect-main" ruleset on biasclear/biasclear.
#
# Run it on your own Mac, after the seed's checks have passed on main. It uses
# GitHub's command-line tool (gh), signed in as you, and does three things:
#   1. Checks that the four required checks (test, security, secret-scan,
#      sast) passed on the newest commit on main. If not, it stops and
#      changes nothing.
#   2. Creates the ruleset "protect-main" (or updates it to match, if it
#      already exists): Active; the default branch; changes only through a
#      pull request, 0 approvals, no code-owner review; the four checks
#      required, each from GitHub Actions; no force pushes; no deletion;
#      nobody may bypass it.
#   3. Reads the ruleset back from GitHub and checks every field.
# It never reads, prints or stores a password, token or key.
#
# Written for macOS's built-in bash 3.2.

set -u

LOG="$HOME/Desktop/biasclear-protect-main.txt"
[ -d "$HOME/Desktop" ] || LOG="$HOME/biasclear-protect-main.txt"
exec > >(tee "$LOG") 2>&1
printf 'Saved to %s\n' "$LOG"

OWNER="biasclear"
REPO="biasclear"
R="repos/$OWNER/$REPO"
NAME="protect-main"
CHECKS="sast secret-scan security test"   # sorted
ACTIONS_APP_ID=15368                      # GitHub Actions
ERR=$(mktemp)

ok=0; failed=0; report=""
say()  { printf '%s\n' "$*"; }
pass() { ok=$((ok+1)); report="$report
  done: $1"; say "  ✓ $1"; }
fail() { failed=$((failed+1)); report="$report
  NOT DONE: $1 ($2)"; say "  ✗ $1: $2"; }
finish() {
  say ""
  say "Report for your PM"
  say "  $ok checks passed, $failed failed.$report"
  rm -f "$ERR"
  exit "$1"
}

say ""
say "BiasClear easy button: ruleset '$NAME' on github.com/$OWNER/$REPO"
say "--------------------------------------------------------------"

# --- Preflight: GitHub's command-line tool, signed in as you -----------------
if ! command -v gh >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then
    say "Installing the GitHub command-line tool (gh) with Homebrew..."
    brew install gh || { say "Couldn't install gh. Tell your PM: 'gh install failed'."; exit 1; }
  else
    say "STOPPED: this needs GitHub's command-line tool (gh), and it isn't installed."
    say "Nothing was changed. Install it from https://cli.github.com , then press the button again."
    exit 1
  fi
fi
if ! gh auth status --hostname github.com >/dev/null 2>&1; then
  if ! { : </dev/tty; } 2>/dev/null; then
    say "STOPPED: gh isn't signed in, and sign-in needs a normal terminal window. Nothing was changed."
    exit 1
  fi
  say "ONE-TIME SIGN-IN: copy the code GitHub prints, press Return, paste it in the browser, confirm with your key."
  gh auth login --hostname github.com --git-protocol https --web </dev/tty || { say "Sign-in didn't finish. Nothing was changed."; exit 1; }
fi
LOGIN=$(gh api user --jq .login 2>/dev/null)
if [ "$LOGIN" != "bws82" ]; then
  say "STOPPED: gh is signed in as '$LOGIN', not bws82. Nothing was changed."
  exit 1
fi
ADMIN=$(gh api "$R" --jq .permissions.admin 2>/dev/null)
if [ "$ADMIN" != "true" ]; then
  say "STOPPED: your account isn't an admin on $OWNER/$REPO (admin=$ADMIN). Nothing was changed."
  exit 1
fi
DEFAULT=$(gh api "$R" --jq .default_branch)
say "Signed in as $LOGIN (admin). Default branch: $DEFAULT."
say ""

# --- 1. The seed's checks passed on main ---------------------------------------
say "1. Required checks on the newest commit on $DEFAULT"
SHA=$(gh api "$R/commits/$DEFAULT" --jq .sha 2>"$ERR") || { fail "read $DEFAULT" "$(head -c 200 "$ERR")"; finish 1; }
say "  commit ${SHA:0:12}"
not_green=""
for c in $CHECKS; do
  # The newest run of this check from GitHub Actions on that commit.
  st=$(gh api "$R/commits/$SHA/check-runs?check_name=$c&per_page=20" \
        --jq "[.check_runs[] | select(.app.id==$ACTIONS_APP_ID)] | sort_by(.started_at) | last | (.status + \"/\" + (.conclusion // \"none\"))" 2>/dev/null)
  if [ "$st" = "completed/success" ]; then
    say "  ✓ $c passed"
  else
    say "  … $c: ${st:-not found}"
    not_green="$not_green $c"
  fi
done
if [ -n "$not_green" ]; then
  fail "checks green on $DEFAULT" "not yet:$not_green. Nothing was changed; press again when they've passed"
  finish 1
fi
pass "all four checks passed on $DEFAULT (${SHA:0:12})"

# --- 2. Create or update the ruleset -------------------------------------------
say "2. Ruleset '$NAME'"
BODY=$(cat <<JSON
{
  "name": "$NAME",
  "target": "branch",
  "enforcement": "active",
  "conditions": { "ref_name": { "include": ["~DEFAULT_BRANCH"], "exclude": [] } },
  "bypass_actors": [],
  "rules": [
    { "type": "pull_request", "parameters": {
        "required_approving_review_count": 0,
        "dismiss_stale_reviews_on_push": false,
        "require_code_owner_review": false,
        "require_last_push_approval": false,
        "required_review_thread_resolution": false } },
    { "type": "required_status_checks", "parameters": {
        "strict_required_status_checks_policy": false,
        "do_not_enforce_on_create": false,
        "required_status_checks": [
          { "context": "test",        "integration_id": $ACTIONS_APP_ID },
          { "context": "security",    "integration_id": $ACTIONS_APP_ID },
          { "context": "secret-scan", "integration_id": $ACTIONS_APP_ID },
          { "context": "sast",        "integration_id": $ACTIONS_APP_ID } ] } },
    { "type": "non_fast_forward" },
    { "type": "deletion" }
  ]
}
JSON
)
ID=$(gh api "$R/rulesets?includes_parents=false&per_page=100" --jq "[.[] | select(.name==\"$NAME\")][0].id // empty" 2>/dev/null)
if [ -n "$ID" ]; then
  if printf '%s' "$BODY" | gh api -X PUT "$R/rulesets/$ID" --input - >/dev/null 2>"$ERR"; then
    pass "ruleset already existed (id $ID); set to match the plan"
  else fail "update ruleset $ID" "$(head -c 300 "$ERR")"; finish 1; fi
else
  ID=$(printf '%s' "$BODY" | gh api -X POST "$R/rulesets" --input - --jq .id 2>"$ERR")
  if [ -n "$ID" ]; then pass "ruleset created (id $ID)"
  else fail "create ruleset" "$(head -c 300 "$ERR")"; finish 1; fi
fi

# --- 3. Read it back and check every field ---------------------------------------
say "3. Read-back from GitHub"
# One read; each line is one field, in a fixed order.
FIELDS=$(gh api "$R/rulesets/$ID" --jq '
  (.rules // []) as $r |
  ([$r[] | select(.type=="pull_request") | .parameters][0] // {}) as $pr |
  [$r[] | select(.type=="required_status_checks") | .parameters.required_status_checks[]] as $sc |
  .name,
  .enforcement,
  .target,
  (.conditions.ref_name.include | join(",")),
  ((.bypass_actors // []) | length | tostring),
  ([$r[].type] | sort | join(",")),
  ($pr.required_approving_review_count | tostring),
  ($pr.require_code_owner_review | tostring),
  ([$sc[].context] | sort | join(" ")),
  ([$sc[].integration_id] | unique | map(tostring) | join(","))' 2>"$ERR") \
  || { fail "read ruleset $ID" "$(head -c 200 "$ERR")"; finish 1; }
n=0
while IFS= read -r got; do
  n=$((n+1))
  case $n in
    1) label="name is $NAME";                         want="$NAME" ;;
    2) label="enforcement Active";                    want="active" ;;
    3) label="targets branches";                      want="branch" ;;
    4) label="applies to the default branch";         want="~DEFAULT_BRANCH" ;;
    5) label="nobody can bypass it";                  want="0" ;;
    6) label="exactly these four rules";              want="deletion,non_fast_forward,pull_request,required_status_checks" ;;
    7) label="pull request required, 0 approvals";    want="0" ;;
    8) label="code-owner review off";                 want="false" ;;
    9) label="required checks: $CHECKS";              want="$CHECKS" ;;
    10) label="each check pinned to GitHub Actions";  want="$ACTIONS_APP_ID" ;;
    *) continue ;;
  esac
  if [ "$got" = "$want" ]; then pass "$label"; else fail "$label" "got '$got', want '$want'"; fi
done <<EOF2
$FIELDS
EOF2
[ "$n" -eq 10 ] || fail "read-back complete" "got $n of 10 fields"
say ""
say "  Ruleset page: https://github.com/$OWNER/$REPO/rules/$ID"

if [ "$failed" -eq 0 ]; then finish 0; else finish 1; fi
