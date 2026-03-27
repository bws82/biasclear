#!/bin/bash
# BiasClear Public Reviewer Check
# Verifies the live public deployment without requiring secrets.

set -euo pipefail

DOMAIN="https://biasclear.com"
PASS=0
FAIL=0

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
echo "  BiasClear Public Reviewer Check"
echo "  Target: $DOMAIN"
echo "  $(date)"
echo "═══════════════════════════════════════════"
echo ""

echo "── Health and Version Truth ──"
HEALTH_JSON=$(curl -s "$DOMAIN/health" 2>/dev/null)
HEALTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$DOMAIN/health" 2>/dev/null)
HEALTH_VERSION=$(echo "$HEALTH_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin).get('version',''))" 2>/dev/null || echo "")
HEALTH_PROVIDER=$(echo "$HEALTH_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin).get('llm_provider_actual',''))" 2>/dev/null || echo "")
HEALTH_LLM=$(echo "$HEALTH_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin).get('llm_available',''))" 2>/dev/null || echo "")
HEALTH_STATUS=$(echo "$HEALTH_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin).get('llm_status',''))" 2>/dev/null || echo "")

check "Health endpoint responds 200" "[ '$HEALTH_CODE' = '200' ]"
check "Health version present" "[ -n '$HEALTH_VERSION' ]"
check "Health reports LLM availability" "[ '$HEALTH_LLM' = 'True' ]"
check "Health reports LLM status" "[ '$HEALTH_STATUS' = 'ready' ] || [ '$HEALTH_STATUS' = 'no_requests_yet' ]"

HEADER_VERSION=$(curl -sI "$DOMAIN/health" | grep -i '^x-biasclear-version:' | tr -d '\r' | cut -d' ' -f2- | head -n 1)
OPENAPI_VERSION=$(curl -s "$DOMAIN/openapi.json" | python3 -c "import sys,json; print(json.load(sys.stdin)['info']['version'])" 2>/dev/null || echo "")

check "Header version matches health" "[ '$HEADER_VERSION' = '$HEALTH_VERSION' ]"
check "OpenAPI version matches health" "[ '$OPENAPI_VERSION' = '$HEALTH_VERSION' ]"

echo ""
echo "── Public Pages ──"
HOME_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$DOMAIN" 2>/dev/null)
DOCS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$DOMAIN/docs" 2>/dev/null)
PRIVACY_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$DOMAIN/privacy" 2>/dev/null)

check "Homepage responds 200" "[ '$HOME_CODE' = '200' ]"
check "API docs respond 200" "[ '$DOCS_CODE' = '200' ]"
check "Privacy page responds 200" "[ '$PRIVACY_CODE' = '200' ]"

echo ""
echo "── Public Playground Scan ──"
TOKEN_JSON=$(curl -s "$DOMAIN/playground/token" 2>/dev/null)
TOKEN=$(echo "$TOKEN_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))" 2>/dev/null || echo "")
check "Playground token issued" "[ -n '$TOKEN' ]"

SCAN_JSON=$(curl -s -X POST "$DOMAIN/scan" \
  -H "Content-Type: application/json" \
  -H "X-Playground-Token: $TOKEN" \
  -d '{"text":"Experts widely agree this is the only responsible path forward.","mode":"full","domain":"general"}' 2>/dev/null)

SCAN_SOURCE=$(echo "$SCAN_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin).get('source',''))" 2>/dev/null || echo "")
SCAN_DEGRADED=$(echo "$SCAN_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin).get('degraded',''))" 2>/dev/null || echo "")
SCAN_MODE=$(echo "$SCAN_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin).get('scan_mode',''))" 2>/dev/null || echo "")
SCAN_SCORE=$(echo "$SCAN_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin).get('truth_score',''))" 2>/dev/null || echo "")
SCAN_FLAGS=$(echo "$SCAN_JSON" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('flags',[])))" 2>/dev/null || echo "")

check "Public scan returns full mode" "[ '$SCAN_MODE' = 'full' ]"
check "Public scan avoids local fallback" "[ '$SCAN_SOURCE' != 'local_fallback' ]"
check "Public scan is not degraded" "[ '$SCAN_DEGRADED' = 'False' ]"
check "Public scan returns a truth score" "[ -n '$SCAN_SCORE' ]"
check "Public scan returns at least one flag on seeded text" "[ '$SCAN_FLAGS' -gt 0 ] 2>/dev/null"

echo ""
echo "═══════════════════════════════════════════"
echo "  Results: $PASS passed, $FAIL failed"
echo "  Version: $HEALTH_VERSION"
echo "  Provider: ${HEALTH_PROVIDER:-unknown}"
echo "═══════════════════════════════════════════"

[ "$FAIL" -eq 0 ] && exit 0 || exit 1
