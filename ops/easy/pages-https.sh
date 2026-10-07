#!/usr/bin/env bash
# BiasClear easy button: HTTPS for biasclear.com, and the github-pages check.
#
# Run it on your own Mac after biasclear.com is pointed at GitHub Pages. It
# uses GitHub's command-line tool (gh), signed in as you, and is safe to press
# again until everything says done:
#   1. Reads the Pages settings. If GitHub has issued the certificate for
#      biasclear.com, it turns on "Enforce HTTPS". If not, it says so and
#      changes nothing; press again later (GitHub usually issues it within an
#      hour of the DNS records pointing at it).
#   2. Checks that the github-pages environment lets only the main branch
#      deploy. If it has no branch rule at all, it adds "main only". It never
#      removes anything; anything unexpected is reported to your PM.
#   3. Once https://biasclear.com/ serves the site, sets the repository's
#      About "Website" link to it.
# It never reads, prints or stores a password, token or key.
#
# Written for macOS's built-in bash 3.2.

set -u

LOG="$HOME/Desktop/biasclear-pages-https.txt"
[ -d "$HOME/Desktop" ] || LOG="$HOME/biasclear-pages-https.txt"
exec > >(tee "$LOG") 2>&1
printf 'Saved to %s\n' "$LOG"

OWNER="biasclear"
REPO="biasclear"
R="repos/$OWNER/$REPO"
DOMAIN="biasclear.com"
SITE="https://$DOMAIN/"
ERR=$(mktemp)

ok=0; failed=0; waiting=0; report=""
say()  { printf '%s\n' "$*"; }
pass() { ok=$((ok+1)); report="$report
  done: $1"; say "  ✓ $1"; }
fail() { failed=$((failed+1)); report="$report
  NOT DONE: $1 ($2)"; say "  ✗ $1: $2"; }
wait_() { waiting=$((waiting+1)); report="$report
  NOT YET: $1 ($2)"; say "  … $1: $2"; }

say ""
say "BiasClear easy button: HTTPS and Pages checks for $DOMAIN"
say "--------------------------------------------------------"

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
say "Signed in as $LOGIN (admin)."
say ""

# --- 1. Enforce HTTPS ------------------------------------------------------------
say "1. HTTPS for $DOMAIN"
PAGES=$(gh api "$R/pages" --jq '[(if (.cname // "") == "" then "none" else .cname end), (.https_enforced|tostring), (.https_certificate.state // "none"), (.build_type // "none")] | join(" ")' 2>"$ERR")
if [ -z "$PAGES" ]; then
  fail "read the Pages settings" "$(head -c 200 "$ERR")"
else
  set -- $PAGES
  CNAME="${1:-}"; ENFORCED="${2:-}"; CERT="${3:-}"; BUILD="${4:-}"
  say "  custom domain: $CNAME; certificate: $CERT; HTTPS enforced: $ENFORCED; source: $BUILD"
  if [ "$CNAME" != "$DOMAIN" ]; then
    fail "custom domain" "Pages says '$CNAME', not $DOMAIN. Nothing was changed; tell your PM"
  elif [ "$ENFORCED" = "true" ]; then
    pass "Enforce HTTPS is already on"
  elif [ "$CERT" = "approved" ]; then
    if printf '{"https_enforced":true}' | gh api -X PUT "$R/pages" --input - >/dev/null 2>"$ERR"; then
      if [ "$(gh api "$R/pages" --jq .https_enforced 2>/dev/null)" = "true" ]; then
        pass "Enforce HTTPS turned on (read back)"
      else fail "Enforce HTTPS" "GitHub accepted the change but the read-back doesn't show it"; fi
    else fail "Enforce HTTPS" "$(head -c 200 "$ERR")"; fi
  else
    wait_ "Enforce HTTPS" "the certificate isn't ready yet (state: $CERT). Nothing was changed; press again in an hour"
  fi
fi

# --- 2. github-pages may deploy from main only -------------------------------------
say "2. The github-pages environment"
ENV=$(gh api "$R/environments/github-pages" --jq '[((.deployment_branch_policy // {}) | if . == {} then "none" else ((.protected_branches|tostring) + "," + (.custom_branch_policies|tostring)) end), ([.protection_rules[]? | select(.type=="required_reviewers")] | length | tostring)] | join(" ")' 2>"$ERR")
if [ -z "$ENV" ]; then
  fail "read the github-pages environment" "$(head -c 200 "$ERR")"
else
  set -- $ENV
  POLICY="${1:-}"; REVIEWERS="${2:-0}"
  rules() { gh api "$R/environments/github-pages/deployment-branch-policies?per_page=100" --jq '[.branch_policies[] | ((.type // "branch") + ":" + .name)] | sort | join(" ")' 2>/dev/null; }
  if [ "$POLICY" = "false,true" ]; then
    RULES=$(rules)
    if [ "$RULES" = "branch:main" ]; then
      pass "github-pages deploys from main only"
    elif [ -z "$RULES" ]; then
      if printf '{"name":"main","type":"branch"}' | gh api -X POST "$R/environments/github-pages/deployment-branch-policies" --input - >/dev/null 2>"$ERR" \
         && [ "$(rules)" = "branch:main" ]; then
        pass "github-pages had no branch rule; added main only (read back)"
      else fail "github-pages main-only rule" "$(head -c 200 "$ERR")"; fi
    else
      fail "github-pages branch rules" "it allows: $RULES (left as it is; tell your PM)"
    fi
  elif [ "$POLICY" = "none" ] && [ "$REVIEWERS" = "0" ]; then
    if printf '{"deployment_branch_policy":{"protected_branches":false,"custom_branch_policies":true}}' \
         | gh api -X PUT "$R/environments/github-pages" --input - >/dev/null 2>"$ERR" \
       && printf '{"name":"main","type":"branch"}' | gh api -X POST "$R/environments/github-pages/deployment-branch-policies" --input - >/dev/null 2>>"$ERR" \
       && [ "$(rules)" = "branch:main" ]; then
      pass "github-pages allowed any branch; now main only (read back)"
    else fail "github-pages main-only rule" "$(head -c 200 "$ERR")"; fi
  else
    fail "github-pages branch rules" "policy '$POLICY', reviewers $REVIEWERS (left as it is; tell your PM)"
  fi
fi

# --- 3. The About "Website" link, once the site answers at biasclear.com ----------
say "3. The repository's Website link"
CODE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "$SITE" 2>/dev/null)
HOME_HTML=$(curl -s --max-time 20 "$SITE" 2>/dev/null | head -c 20000)
case "$HOME_HTML" in *BiasClear*) LOOKS=yes ;; *) LOOKS=no ;; esac
if [ "$CODE" = "200" ] && [ "$LOOKS" = "yes" ]; then
  say "  $SITE answers with the site."
  NOW=$(gh api "$R" --jq '.homepage // ""' 2>/dev/null)
  if [ "$NOW" = "$SITE" ]; then
    pass "Website link is already $SITE"
  elif printf '{"homepage":"%s"}' "$SITE" | gh api -X PATCH "$R" --input - >/dev/null 2>"$ERR" \
       && [ "$(gh api "$R" --jq '.homepage // ""' 2>/dev/null)" = "$SITE" ]; then
    pass "Website link set to $SITE (was '${NOW:-empty}')"
  else fail "Website link" "$(head -c 200 "$ERR")"; fi
else
  wait_ "Website link" "$SITE doesn't serve the site yet (HTTP ${CODE:-none}). Nothing was changed; press again later"
fi

say ""
say "Report for your PM"
say "  $ok done, $waiting not yet, $failed need your PM.$report"
rm -f "$ERR"
[ "$failed" -eq 0 ] || exit 1
exit 0
