#!/bin/bash
# Launch the polling service as a daemon (background process)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check Python
if ! command -v python3.11 &>/dev/null; then
    echo "Error: Python 3.11+ required"
    exit 1
fi

# Use venv if available
PYTHON="python3.11"
if [ -x ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
fi

# Check if config exists, create from example if not
if [ ! -f "config/polling_service.yaml" ]; then
    echo "Creating default polling service config..."
    mkdir -p config
    cp config/automation_rules.yaml.example config/automation_rules.yaml 2>/dev/null || true
fi

# Environment setup
export OPENCLAW_SESSION_KEY="${OPENCLAW_SESSION_KEY:-}"

echo "Starting polling service..."
echo "Config: config/polling_service.yaml"
echo "Log output will be to stdout/stderr"
echo ""

# Run the service
exec "$PYTHON" polling_service.py "$@"
