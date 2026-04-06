#!/bin/bash
set -e

echo "================================================"
echo "OpenClaw Things Sentiment Integration - Setup"
echo "================================================"

# Check Python version
echo "Checking Python..."
python3 --version || { echo "Python 3.11+ required"; exit 1; }

# Install dependencies
echo "Installing dependencies..."
pip3 install --upgrade pip
pip3 install -r requirements-test.txt

# Try to install UI dependencies (may fail on Linux)
echo "Installing UI dependencies (macOS only)..."
pip3 install rumps pync 2>/dev/null || echo "Note: rumps/pync require macOS"

# Run full verification
echo "Running verification pipeline..."
chmod +x scripts/verify_poller.sh
bash scripts/verify_poller.sh

# Copy demo to production memory
echo "Setting up production memory..."
cp -f memory_demo.json memory.json

echo "================================================"
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Launch UI (macOS): make ui"
echo "  2. Test messaging: make send-test SESSION_ID=<your-openclaw-session>"
echo "  3. Run tests: pytest -v"
echo ""
echo "See QUICKSTART.md for detailed usage instructions."
