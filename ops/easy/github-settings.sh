#!/usr/bin/env bash
# BiasClear easy button: repository settings for biasclear/biasclear.
#
# Run it on your own Mac. It uses the GitHub command-line tool (gh), signed in
# as you, and changes only the settings listed below. It never reads, prints or
# stores a password, token or key. Safe to run again: each step checks first.
#
# What it sets:
#   1. Automatic checks are read-only by default and can't approve pull requests.
#   2. The "pypi" release environment waits for your approval, for v* tags only.
#   3. GitHub's free security features: Dependabot alerts, private vulnerability
#      reporting, secret scanning and push protection.
#   4. The website is published by a workflow (GitHub Pages, source: Actions).
#   5. The repository's description, topics and tidy defaults.
#
# Written for macOS's built-in bash 3.2.

set -u

OWNER="biasclear"
REPO="biasclear"
R="repos/$OWNER/$REPO"
DESCRIPTION="Marks the persuasion moves in any text, in your browser. Same rules for everyone, tested in public."
TOPICS='["persuasion","rhetoric","media-literacy","critical-thinking","bias-detection","open-source","python","typescript"]'

ok=0; failed=0; report=""
say()  { printf '%s\n' "$*"; }
pass() { ok=$((ok+1)); report="$report
  done: $1"; say "  ✓ $1"; }
fail() { failed=$((failed+1)); report="$report
  NOT DONE: $1 ($2)"; say "  ✗ $1: $2"; }

say ""
say "BiasClear easy button: settings for github.com/$OWNER/$REPO"
say "-------------------------------------------------------------"

# --- Preflight: the GitHub command-line tool, signed in as you -------------
if ! command -v gh >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then
    say "Installing the GitHub command-line tool (gh) with Homebrew..."
    brew install gh || { say "Couldn't install gh. Tell your PM: 'gh install failed'."; exit 1; }
  else
    say "This needs the GitHub command-line tool (gh)."
    say "Install it from https://cli.github.com (download the macOS installer,"
    say "double-click it), then press the button again."
    exit 1
  fi
fi

if ! gh auth status --hostname github.com >/dev/null 2>&1; then
  say "Signing you in to GitHub. A browser window opens: confirm with your key."
  gh auth login --hostname github.com --git-protocol https --web || { say "Sign-in didn't finish. Press the button again."; exit 1; }
fi

LOGIN=$(gh api user --jq .login 2>/dev/null)
if [ "$LOGIN" != "bws82" ]; then
  say "gh is signed in as '$LOGIN', not bws82. Run: gh auth switch  (or gh auth login), then press the button again."
  exit 1
fi
USER_ID=$(gh api user --jq .id)
ADMIN=$(gh api "$R" --jq .permissions.admin 2>/dev/null)
if [ "$ADMIN" != "true" ]; then
  say "Your account can't change settings on $OWNER/$REPO (admin=$ADMIN). Tell your PM."
  exit 1
fi
say "Signed in as $LOGIN (admin on $OWNER/$REPO)."
say ""

# --- 1. Automatic checks: read-only, can't approve pull requests -------------
say "1. Automatic checks"
if printf '{"default_workflow_permissions":"read","can_approve_pull_request_reviews":false}' \
   | gh api -X PUT "$R/actions/permissions/workflow" --input - >/dev/null 2>/tmp/bc-err; then
  pass "checks are read-only and can't approve pull requests"
else fail "checks read-only" "$(head -c 200 /tmp/bc-err)"; fi

# --- 2. Release approval switch ------------------------------------------------
say "2. Release approval (environment 'pypi')"
if printf '{"wait_timer":0,"prevent_self_review":false,"reviewers":[{"type":"User","id":%s}],"deployment_branch_policy":{"protected_branches":false,"custom_branch_policies":true}}' "$USER_ID" \
   | gh api -X PUT "$R/environments/pypi" --input - >/dev/null 2>/tmp/bc-err; then
  pass "releases wait for your approval (reviewer: $LOGIN)"
  HAVE=$(gh api "$R/environments/pypi/deployment-branch-policies" --jq '[.branch_policies[] | select(.name=="v*" and .type=="tag")] | length' 2>/dev/null)
  if [ "$HAVE" = "1" ]; then
    pass "release tag rule v* already present"
  elif printf '{"name":"v*","type":"tag"}' | gh api -X POST "$R/environments/pypi/deployment-branch-policies" --input - >/dev/null 2>/tmp/bc-err; then
    pass "release tag rule v* added"
  else fail "release tag rule v*" "$(head -c 200 /tmp/bc-err)"; fi
  OTHERS=$(gh api "$R/environments/pypi/deployment-branch-policies" --jq '[.branch_policies[] | select(.name!="v*" or .type!="tag") | .name] | join(", ")' 2>/dev/null)
  [ -n "$OTHERS" ] && fail "extra deployment rules found" "$OTHERS (left as they are; tell your PM)"
else fail "release approval environment" "$(head -c 200 /tmp/bc-err)"; fi

# --- 3. Free security features -------------------------------------------------
say "3. Security features"
if gh api -X PUT "$R/vulnerability-alerts" >/dev/null 2>/tmp/bc-err; then pass "Dependabot alerts on"
else fail "Dependabot alerts" "$(head -c 200 /tmp/bc-err)"; fi
if gh api -X PUT "$R/private-vulnerability-reporting" >/dev/null 2>/tmp/bc-err; then pass "private vulnerability reporting on"
else fail "private vulnerability reporting" "$(head -c 200 /tmp/bc-err)"; fi
if printf '{"security_and_analysis":{"secret_scanning":{"status":"enabled"},"secret_scanning_push_protection":{"status":"enabled"}}}' \
   | gh api -X PATCH "$R" --input - >/dev/null 2>/tmp/bc-err; then
  pass "secret scanning and push protection on"
else fail "secret scanning and push protection" "$(head -c 200 /tmp/bc-err)"; fi

# --- 4. Website published by a workflow -----------------------------------
say "4. Website (GitHub Pages)"
if gh api "$R/pages" >/dev/null 2>&1; then
  if printf '{"build_type":"workflow"}' | gh api -X PUT "$R/pages" --input - >/dev/null 2>/tmp/bc-err; then
    pass "Pages source is GitHub Actions"
  else fail "Pages source" "$(head -c 200 /tmp/bc-err)"; fi
else
  if printf '{"build_type":"workflow"}' | gh api -X POST "$R/pages" --input - >/dev/null 2>/tmp/bc-err; then
    pass "Pages turned on, source GitHub Actions"
  else fail "Pages source" "$(head -c 200 /tmp/bc-err)"; fi
fi

# --- 5. Description, topics, tidy defaults ----------------------------------
say "5. Repository page"
if printf '{"description":"%s","has_wiki":false,"has_projects":false,"delete_branch_on_merge":true,"allow_auto_merge":false}' "$DESCRIPTION" \
   | gh api -X PATCH "$R" --input - >/dev/null 2>/tmp/bc-err; then
  pass "description and defaults set"
else fail "description and defaults" "$(head -c 200 /tmp/bc-err)"; fi
if printf '{"names":%s}' "$TOPICS" | gh api -X PUT "$R/topics" --input - >/dev/null 2>/tmp/bc-err; then
  pass "topics set"
else fail "topics" "$(head -c 200 /tmp/bc-err)"; fi

rm -f /tmp/bc-err

# --- Read-back -----------------------------------------------------------------
say ""
say "Read-back from GitHub:"
say "  checks default:  $(gh api "$R/actions/permissions/workflow" --jq '.default_workflow_permissions + ", can approve PRs: " + (.can_approve_pull_request_reviews|tostring)' 2>/dev/null)"
say "  pypi reviewers:  $(gh api "$R/environments/pypi" --jq '[.protection_rules[]? | select(.type=="required_reviewers") | .reviewers[]?.reviewer.login] | join(", ")' 2>/dev/null)"
say "  pypi rules:      $(gh api "$R/environments/pypi/deployment-branch-policies" --jq '[.branch_policies[] | .type + " " + .name] | join(", ")' 2>/dev/null)"
say "  pages:           $(gh api "$R/pages" --jq '.build_type' 2>/dev/null)"
say "  topics:          $(gh api "$R/topics" --jq '.names | join(", ")' 2>/dev/null)"

say ""
say "-------------------------------------------------------------"
say "Finished: $ok done, $failed not done."
say "Copy everything from 'Report for your PM' down and paste it to your PM."
say ""
say "Report for your PM (no secrets in it):$report"
say ""
