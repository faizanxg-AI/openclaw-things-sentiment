# OpenClaw Communication Architecture

## Overview

This project uses a **direct CLI** strategy for OpenClaw communication to avoid MCP `structuredContent` incompatibility issues with generic MCP clients.

## Why Direct CLI?

The OpenClaw MCP bridge returns data in Claude Code's proprietary `structuredContent` extension, which generic MCP clients (like Hermes) cannot parse. While tool discovery works, actual tool responses yield only plain text placeholders, making MCP unusable. Therefore, all production communication uses the OpenClaw CLI directly.

## Two Communication Layers

### 1. Poller Layer
The poller (`things_sentiment_poller.py`) is primarily independent:
- Calls `things completed --json` directly (no OpenClaw involvement)
- Writes results to local `memory.json`
- **Optional OpenClaw integration**: If the environment variable `OPENCLAW_SESSION_KEY` is set, the poller sends a summary message to that OpenClaw session after each successful run using `openclaw agent --session-id`. This enables automatic agent notification of new sentiment data.
- Standalone, reliable, can run without OpenClaw

### 2. OpenClaw Integration Layer (UI)
The rumps menu bar app (`rumps_app/main.py`) integrates with OpenClaw for agent-to-agent communication:
- **Discovery**: `openclaw sessions --json` to list active sessions
- **Sending**: `openclaw agent --session-id <key> --message <text> --json` to send messages to an agent
- **Receiving**: Not yet implemented; UI currently reads from local `memory.json` only
- The UI automatically selects the most recently updated session as `current_session`
- Test notifications use the selected session to send a message via OpenClaw

## Verification Checklist

- [ ] `openclaw` binary is in PATH (`which openclaw`)
- [ ] `openclaw sessions --json` returns valid JSON with at least one session
- [ ] `openclaw agent --session-id <key> --message "test" --json` sends successfully (requires active session)
- [ ] Poller can run independently with `--demo` flag
- [ ] UI launches on macOS (`make ui`) and shows session count
- [ ] Optional: Set `OPENCLAW_SESSION_KEY` and run poller to verify automatic summary message arrives in target session

## Test Sequence (Verified)

1. `python3 things_sentiment_poller.py --demo --demo-count 15 --use-demo`
   Generates `memory_demo.json` with edge cases and copies to `memory.json`.

2. `python3 comprehensive_validator.py`
   Validates memory schema, required fields, and emotion mapping.

3. `openclaw sessions --json`
   Lists active sessions to verify OpenClaw is running.

4. `openclaw agent --session-id <key> --message "Hello" --json`
   Send a test message to an active session.

5. Optional: Set `OPENCLAW_SESSION_KEY` environment variable and re-run the poller to test automatic summary delivery.

6. Launch rumps UI: `python3 -m rumps_app.main` (macOS GUI required)

## Known Issues & Fixes

- **MCP structuredContent incompatibility**: The `openclaw` MCP server returns Claude Code's proprietary `structuredContent` which cannot be parsed by generic MCP clients. Use direct CLI path for all data operations.
- **OpenClaw CLI syntax**: Earlier versions used `openclaw message send` with positional arguments; the correct form is `openclaw agent --session-id <key> --message <text> --json`. The codebase has been updated accordingly.

## Quick Reference

```bash
# Full verification
make verify

# Run pytest suite
make test

# Generate demo memory
make demo

# Launch UI (macOS)
make ui

# Manual OpenClaw send (requires SESSION_KEY env var)
openclaw agent --session-id "$SESSION_KEY" --message "Hello from Hermes" --json
```

## Notes

- Do NOT rely on MCP `events_wait` or `messages_*` tools for data retrieval
- The only MCP tools that work reliably are permissions and resource reads
- All production communication should use direct CLI path
- State persistence: `poller_state.json` stores `last_poll` and `last_task_id` to avoid duplicates across restarts
- The UI auto-refreshes the OpenClaw session list every 60 seconds and uses the most recent session for outbound messages
