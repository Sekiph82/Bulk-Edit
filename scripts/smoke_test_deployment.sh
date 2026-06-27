#!/bin/bash
# Smoke test a Bulk-Edit deployment.
# Usage: ./scripts/smoke_test_deployment.sh <frontend_url> <backend_url>
# Example: ./scripts/smoke_test_deployment.sh http://localhost:3100 http://localhost:8100

set -euo pipefail

FRONTEND_URL="${1:-http://localhost:3100}"
BACKEND_URL="${2:-http://localhost:8100}"

PASS="\033[32mPASS\033[0m"
FAIL="\033[31mFAIL\033[0m"
passed=0
failed=0
report=()

check_status() {
    local name="$1" url="$2" expected="${3:-200}"
    local code
    code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 "$url" 2>/dev/null || echo "000")
    if [ "$code" = "$expected" ]; then
        passed=$((passed+1))
        report+=("  PASS  $name ($code)")
    else
        failed=$((failed+1))
        report+=("  FAIL  $name — expected $expected, got $code")
    fi
}

check_json() {
    local name="$1" url="$2" field="$3" expected="$4"
    local body actual
    body=$(curl -s --max-time 15 "$url" 2>/dev/null || echo "{}")
    actual=$(python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('$field',''))" <<< "$body" 2>/dev/null || echo "")
    if [ "$actual" = "$expected" ]; then
        passed=$((passed+1))
        report+=("  PASS  $name ($field=$actual)")
    else
        failed=$((failed+1))
        report+=("  FAIL  $name — $field expected '$expected' got '$actual'")
    fi
}

echo ""
echo "============================================================"
echo "  Bulk-Edit Deployment Smoke Test"
echo "  Frontend: $FRONTEND_URL"
echo "  Backend:  $BACKEND_URL"
echo "============================================================"
echo ""

check_json "Backend /health"       "$BACKEND_URL/api/v1/health"       "status" "ok"
check_json "Backend /health/ready" "$BACKEND_URL/api/v1/health/ready" "status" "ready"

for route in "/" "/pricing" "/features" "/faq" "/contact-us" "/login" "/register" \
             "/dashboard" "/admin" "/shops" "/listings"; do
    check_status "Frontend $route" "$FRONTEND_URL$route"
done

echo ""
for line in "${report[@]}"; do
    echo -e "$line"
done
echo ""
echo "============================================================"
if [ "$failed" -eq 0 ]; then
    echo -e "  ${PASS}  All $passed checks passed"
else
    echo -e "  ${FAIL}  $passed passed, $failed failed"
fi
echo "============================================================"
echo ""

[ "$failed" -eq 0 ] && exit 0 || exit 1
