#!/usr/bin/env bash
set -euo pipefail

# OpenClaw Poller Verification Script
# Runs the full verification sequence to ensure poller and OpenClaw integration are working

WORKSPACE="/Users/faizan/agent-bridge/workspace"
cd "$WORKSPACE"

echo "=== Step 1: Generate demo memory ==="
python3 things_sentiment_poller.py --demo --demo-count 15 --use-demo

echo "=== Step 2: Validate memory schema ==="
python3 comprehensive_validator.py

echo "=== Step 3: Check OpenClaw CLI availability ==="
if ! command -v openclaw &>/dev/null; then
    echo "ERROR: openclaw binary not found in PATH"
    exit 1
fi
echo "openclaw found: $(which openclaw)"

echo "=== Step 4: Test OpenClaw sessions JSON output ==="
if openclaw sessions --json >/dev/null 2>&1; then
    echo "sessions command succeeded (may return empty list)"
else
    echo "WARNING: sessions command failed or timed out (non-fatal)"
fi

echo "=== Step 5: Verify rumps dependencies (macOS only) ==="
if [[ "$(uname)" == "Darwin" ]]; then
    python3 -c "import rumps" 2>/dev/null && echo "rumps available" || echo "WARNING: rumps not installed (run: pip install rumps pync)"
else
    echo "Non-macOS system: skipping rumps check"
fi

echo "=== Verification complete ==="
echo "Memory file generated: $WORKSPACE/memory_demo.json"
echo "To send a test message, use: scripts/send_test_message.sh <session_id> \"your message\""
