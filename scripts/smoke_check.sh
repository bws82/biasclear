#!/bin/bash
# BiasClear Public Smoke Check
# Verifies the public deployment is healthy and producing correct results.
# Usage: ./scripts/smoke_check.sh [API_KEY]

set -euo pipefail

DOMAIN="https://biasclear.com"
API_KEY="${1:-${BIASCLEAR_API_KEY:-}}"
PASS=0
FAIL=0

if [ -z "$API_KEY" ]; then
  echo "Error: API key required."
  echo "Usage: ./scripts/smoke_check.sh <API_KEY>"
  echo "   or: BIASCLEAR_API_KEY=... ./scripts/smoke_check.sh"
  exit 1
fi

green() { printf "\033[32m✓ %s\033[0m\n" "$1"; }
red()   { printf "\033[31m✗ %s\033[0m\n" "$1"; }

check() {
  local desc="$1" condition="$2"
  if eval "$condition"; then
    green "$desc"; PASS=$((PASS+1))
  else
    red "$desc"; FAIL=$((FAIL+1))
  fi
}

echo "═══════════════════════════════════════════"
echo "  BiasClear Public Smoke Check"
echo "  Target: $DOMAIN"
echo "  $(date)"
echo "═══════════════════════════════════════════"
echo ""

# 1. Health check
echo "── Health ──"
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$DOMAIN/health" 2>/dev/null)
check "Health endpoint responds 200" "[ '$HEALTH' = '200' ]"

# 2. Playground token flow
echo ""
echo "── Playground Auth ──"
TOKEN_RESP=$(curl -s "$DOMAIN/playground/token" 2>/dev/null)
TOKEN=$(echo "$TOKEN_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))" 2>/dev/null || echo "")
check "Playground token issued" "[ -n '$TOKEN' ]"

# 3. Full mode scan — legal positive
echo ""
echo "── Legal Positive (should flag) ──"
LEGAL=$(curl -s "$DOMAIN/scan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"text": "It is well-settled law that these claims are plainly meritless and should be dismissed with sanctions.", "mode": "full", "domain": "legal"}' 2>/dev/null)

LEGAL_MODE=$(echo "$LEGAL" | python3 -c "import sys,json; print(json.load(sys.stdin).get('scan_mode',''))" 2>/dev/null)
LEGAL_SOURCE=$(echo "$LEGAL" | python3 -c "import sys,json; print(json.load(sys.stdin).get('source',''))" 2>/dev/null)
LEGAL_DEGRADED=$(echo "$LEGAL" | python3 -c "import sys,json; print(json.load(sys.stdin).get('degraded',''))" 2>/dev/null)
LEGAL_SCORE=$(echo "$LEGAL" | python3 -c "import sys,json; print(json.load(sys.stdin).get('truth_score',''))" 2>/dev/null)
LEGAL_FLAGS=$(echo "$LEGAL" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('flags',[])))" 2>/dev/null)

check "scan_mode = full" "[ '$LEGAL_MODE' = 'full' ]"
check "source is not local_fallback" "[ '$LEGAL_SOURCE' != 'local_fallback' ]"
check "degraded = False" "[ '$LEGAL_DEGRADED' = 'False' ]"
check "Legal example flagged (score < 80)" "[ '$LEGAL_SCORE' -lt 80 ] 2>/dev/null"
check "Legal example has flags" "[ '$LEGAL_FLAGS' -gt 0 ] 2>/dev/null"

# 4. Causal blame positive
echo ""
echo "── Causal Blame Positive (should flag) ──"
CAUSAL=$(curl -s "$DOMAIN/scan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"text": "Trump is ruining everything this country stands for.", "mode": "full"}' 2>/dev/null)

CAUSAL_PIDS=$(echo "$CAUSAL" | python3 -c "import sys,json; pids=[f['pattern_id'] for f in json.load(sys.stdin).get('flags',[])]; print(','.join(pids))" 2>/dev/null)
check "CAUSAL_TOTALIZATION fires" "echo '$CAUSAL_PIDS' | grep -q 'CAUSAL_TOTALIZATION'"

# 5. Bounded clean control (should NOT flag causal patterns)
echo ""
echo "── Bounded Clean Control (should stay clean) ──"
CLEAN=$(curl -s "$DOMAIN/scan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"text": "The policy caused me to lose my health insurance.", "mode": "full"}' 2>/dev/null)

CLEAN_PIDS=$(echo "$CLEAN" | python3 -c "import sys,json; pids=[f['pattern_id'] for f in json.load(sys.stdin).get('flags',[]) if 'CAUSAL' in f['pattern_id'] or 'MONOCAUSAL' in f['pattern_id'] or 'TOTALIZING' in f['pattern_id']]; print(','.join(pids) if pids else 'none')" 2>/dev/null)
check "No causal-blame false positives" "[ '$CLEAN_PIDS' = 'none' ]"

# Summary
echo ""
echo "═══════════════════════════════════════════"
echo "  Results: $PASS passed, $FAIL failed"
echo "═══════════════════════════════════════════"

[ "$FAIL" -eq 0 ] && exit 0 || exit 1
