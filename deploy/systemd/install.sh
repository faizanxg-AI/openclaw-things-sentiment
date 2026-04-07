#!/bin/bash
# Install the systemd service with proper paths

set -e

# Determine workspace directory
if [ -z "$WORKDIR" ]; then
    # Try to auto-detect from script location
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    WORKDIR="${1:-$SCRIPT_DIR}"
fi

WORKDIR="$(realpath "$WORKDIR")"

echo "Installing systemd service with WORKDIR=$WORKDIR"

SYSTEMD_DIR="$HOME/.config/systemd/user"
mkdir -p "$SYSTEMD_DIR"

# Replace placeholders in service file
SERVICE_TEMPLATE="$(dirname "$0")/things-sentiment-poller.service"
SERVICE_FILE="$SYSTEMD_DIR/things-sentiment-poller.service"

# Create customized service file
sed "s|\${WORKDIR:-/path/to/agent-bridge/workspace}|$WORKDIR|g" "$SERVICE_TEMPLATE" > "$SERVICE_FILE"

echo "Service file created: $SERVICE_FILE"
echo "To start the service:"
echo "  systemctl --user daemon-reload"
echo "  systemctl --user enable --now things-sentiment-poller"
echo "  systemctl --user status things-sentiment-poller"
