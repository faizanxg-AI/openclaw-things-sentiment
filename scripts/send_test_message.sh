#!/usr/bin/env bash
set -euo pipefail

# Send a test message via OpenClaw agent CLI
# Usage: scripts/send_test_message.sh <session_id> "<message>"

if [[ $# -ne 2 ]]; then
    echo "Usage: $0 <session_id> \"<message>\""
    echo "Example: $0 abc123 \"Hello from Hermes verification\""
    exit 1
fi

SESSION_ID="$1"
MESSAGE="$2"

echo "Sending message to OpenClaw session: $SESSION_ID"
echo "Message: $MESSAGE"

openclaw agent --session-id "$SESSION_ID" --message "$MESSAGE" --json
