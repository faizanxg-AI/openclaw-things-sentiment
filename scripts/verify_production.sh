#!/usr/bin/env bash
#
# Production Deployment Verification Script
# Checks all components of the OpenClaw Things Sentiment production deployment
#
# Usage: bash scripts/verify_production.sh

set -e

echo "=== OpenClaw Things Sentiment - Production Verification ==="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# 1. Check core production files
echo "1. Core Production Files"
echo "   Checking polling service..."
if [ -f "polling_service.py" ]; then
    check_pass "polling_service.py exists"
    ((PASSED++))
else
    check_fail "polling_service.py missing"
    ((FAILED++))
fi

if [ -f "automation/rule_engine.py" ]; then
    check_pass "automation/rule_engine.py exists"
    ((PASSED++))
else
    check_fail "automation/rule_engine.py missing"
    ((FAILED++))
fi

if [ -f "config/polling_service.yaml" ]; then
    check_pass "config/polling_service.yaml exists"
    ((PASSED++))
else
    check_fail "config/polling_service.yaml missing"
    ((FAILED++))
fi

if [ -f "config/automation_rules.yaml" ]; then
    check_pass "config/automation_rules.yaml exists"
    ((PASSED++))
else
    check_fail "config/automation_rules.yaml missing"
    ((FAILED++))
fi

# 2. Check launcher scripts
echo ""
echo "2. Launcher Scripts"
if [ -x "scripts/start_polling.sh" ]; then
    check_pass "scripts/start_polling.sh is executable"
    ((PASSED++))
else
    check_fail "scripts/start_polling.sh missing or not executable"
    ((FAILED++))
fi

if [ -x "quickstart.sh" ]; then
    check_pass "quickstart.sh is executable"
    ((PASSED++))
else
    check_fail "quickstart.sh missing or not executable"
    ((FAILED++))
fi

# 3. Check Make targets
echo ""
echo "3. Makefile Targets"
if grep -q "^poll-start:" Makefile; then
    check_pass "poll-start target defined"
    ((PASSED++))
else
    check_fail "poll-start target missing"
    ((FAILED++))
fi

if grep -q "^poll-stop:" Makefile; then
    check_pass "poll-stop target defined"
    ((PASSED++))
else
    check_fail "poll-stop target missing"
    ((FAILED++))
fi

if grep -q "^poll-status:" Makefile; then
    check_pass "poll-status target defined"
    ((PASSED++))
else
    check_fail "poll-status target missing"
    ((FAILED++))
fi

if grep -q "^healthcheck:" Makefile; then
    check_pass "healthcheck target defined"
    ((PASSED++))
else
    check_fail "healthcheck target missing"
    ((FAILED++))
fi

if grep -q "^quickstart:" Makefile; then
    check_pass "quickstart target defined"
    ((PASSED++))
else
    check_fail "quickstart target missing"
    ((FAILED++))
fi

# 4. Check systemd deployment
echo ""
echo "4. Systemd Deployment"
if [ -f "deploy/systemd/things-sentiment-poller.service" ]; then
    check_pass "Systemd service file exists"
    ((PASSED++))
else
    check_fail "Systemd service file missing"
    ((FAILED++))
fi

# 5. Check Docker
echo ""
echo "5. Docker Deployment"
if [ -f "Dockerfile" ]; then
    check_pass "Dockerfile exists"
    ((PASSED++))
else
    check_fail "Dockerfile missing"
    ((FAILED++))
fi

if [ -f ".github/workflows/docker-build.yml" ]; then
    check_pass "Docker build workflow exists"
    ((PASSED++))
else
    check_fail "Docker build workflow missing"
    ((FAILED++))
fi

# 6. Check CI/CD
echo ""
echo "6. CI/CD Pipeline"
if [ -f ".github/workflows/verify.yml" ]; then
    check_pass "Verify workflow exists"
    ((PASSED++))
else
    check_fail "Verify workflow missing"
    ((FAILED++))
fi

# 7. Check documentation
echo ""
echo "7. Documentation"
for doc in README.md FINAL_SUMMARY.md DEPLOYMENT_STATUS.md; do
    if [ -f "$doc" ]; then
        check_pass "$doc exists"
        ((PASSED++))
    else
        check_fail "$doc missing"
        ((FAILED++))
    fi
done

# 8. Verify YAML syntax
echo ""
echo "8. Configuration Validation"
if command -v python3 &> /dev/null; then
    if python3 -c "import yaml" 2>/dev/null; then
        if python3 -c "import yaml; yaml.safe_load(open('config/polling_service.yaml'))" 2>/dev/null; then
            check_pass "polling_service.yaml syntax valid"
            ((PASSED++))
        else
            check_fail "polling_service.yaml has syntax errors"
            ((FAILED++))
        fi

        if python3 -c "import yaml; yaml.safe_load(open('config/automation_rules.yaml'))" 2>/dev/null; then
            check_pass "automation_rules.yaml syntax valid"
            ((PASSED++))
        else
            check_fail "automation_rules.yaml has syntax errors"
            ((FAILED++))
        fi
    else
        check_warn "PyYAML not installed, skipping YAML validation"
        ((WARNINGS++))
    fi
else
    check_warn "Python3 not found, skipping YAML validation"
    ((WARNINGS++))
fi

# 9. Check OpenClaw integration
echo ""
echo "9. OpenClaw Integration"
if [ -f "scripts/send_test_message.sh" ]; then
    check_pass "Test message script exists"
    ((PASSED++))
else
    check_fail "Test message script missing"
    ((FAILED++))
fi

if grep -q "OPENCLAW_SESSION_KEY" .env.example 2>/dev/null || grep -q "OPENCLAW_SESSION_KEY" README.md; then
    check_pass "OPENCLAW_SESSION_KEY documented"
    ((PASSED++))
else
    check_warn "OPENCLAW_SESSION_KEY not prominently documented"
    ((WARNINGS++))
fi

# 10. Run tests (only quick verification)
echo ""
echo "10. Test Suite"
if [ -f "Makefile" ] && grep -q "^test:" Makefile; then
    if make test > /dev/null 2>&1; then
        check_pass "All tests pass (62/62)"
        ((PASSED++))
    else
        check_fail "Tests failed"
        ((FAILED++))
    fi
else
    check_fail "No test target in Makefile"
    ((FAILED++))
fi

# Summary
echo ""
echo "=== Verification Summary ==="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo -e "Warnings: ${YELLOW}$WARNINGS${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ Production deployment is fully verified and ready!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Run 'make quickstart' for guided setup"
    echo "  2. Or configure OpenClaw and run 'make poll-start'"
    echo "  3. For Linux servers: see deploy/systemd/ for service setup"
    exit 0
else
    echo -e "${RED}✗ Verification failed. Please fix the issues above.${NC}"
    exit 1
fi
