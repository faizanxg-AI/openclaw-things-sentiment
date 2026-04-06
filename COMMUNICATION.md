# OpenClaw Communication Architecture

## Overview

This project uses a **direct CLI fallback** strategy for OpenClaw communication to avoid MCP `structuredContent` incompatibility issues with generic MCP clients.

## Why CLI Fallback?

The OpenClaw MCP bridge returns data in Claude Code's proprietary `structuredContent` extension, which generic MCP clients (like Hermes) cannot parse. While tool discovery works, actual tool responses yield only plain text placeholders, making MCP unusable.

## Two Communication Layers

### 1. Poller Layer
The poller (`things_sentiment_poller.py`) operates completely independently:
- Calls `things completed --json` directly (no OpenClaw involvement)
- Writes results to local `memory.json`
- Standalone, reliable, no external dependencies

### 2. OpenClaw Integration Layer
Agent-to-agent communication uses OpenClaw's direct CLI:
- Use `openclaw agent --session-id <id>` for agent turns
- Use `openclaw sessions --json` to discover active sessions
- CLI outputs standard JSON, no `structuredContent` parsing needed
- This path is stable and working

## Verification Checklist

- [ ] `openclaw` binary is in PATH (`which openclaw`)
- [ ] `openclaw sessions --json` returns valid JSON
- [ ] `openclaw agent --help` shows correct usage
- [ ] Poller can run independently with `--demo` flag

## Test Sequence (Verified)

1. `python3 things_sentiment_poller.py --demo --demo-count 15 --use-demo`  
   Generates `memory_demo.json` with edge cases. The `--use-demo` flag tells the poller to use the demo dataset pattern (avoids needing live Things data). Note: Fixed bug where `memory_path` was undefined in demo mode.

2. `python3 comprehensive_validator.py`  
   Validates memory schema, required fields, and emotion mapping. Should pass with the updated demo data (empty titles replaced with `(Untitled task)`).

3. `openclaw agent --session-id <id> --message "test" --json`  
   Sends a test message through OpenClaw agent interface and receives JSON response. Verifies two-way communication.

4. `openclaw sessions --json`  
   Lists active sessions to discover session IDs.

5. Launch rumps UI: `python3 -m rumps_app.main` (macOS GUI required)

## Known Issues & Fixes

- **MCP structuredContent incompatibility**: The `openclaw` MCP server returns Claude Code's proprietary `structuredContent` which cannot be parsed by generic MCP clients. Use direct CLI fallback for all data operations.
- **Poller demo mode bug**: When using `--demo` without explicit `--output`, `memory_path` was undefined. Fixed by setting `memory_path = WORKSPACE / "memory_demo.json"` in the demo branch.

## Quick Reference

[![Verification](https://github.com/openclaw/agent-bridge/actions/workflows/verify.yml/badge.svg)](https://github.com/openclaw/agent-bridge/actions?query=workflow%3AVerification)

```bash
# Full verification
make verify

# Run pytest suite
make test

# Generate demo memory
make demo

# Send test OpenClaw message
make openclaw-send SESSION_ID="abc123" MESSAGE="Hello"

# Install dependencies
make install

# Clean ephemeral files
make clean
```

## Notes

- Do NOT rely on MCP `events_wait` or `messages_*` tools for data retrieval
- The only MCP tools that work reliably are permissions and resource reads
- All production communication should use direct CLI path
- State persistence: `poller_state.json` stores `last_poll` and `last_task_id` to avoid duplicates across restarts
