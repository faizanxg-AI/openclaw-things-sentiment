# OpenClaw Integration Quickstart

This guide walks through setting up and verifying the Things sentiment poller with OpenClaw agent-to-agent communication.

## Prerequisites

- macOS (for rumps UI) or Linux (for headless verification)
- Python 3.11+
- OpenClaw CLI (`openclaw`) installed and in PATH
- Homebrew packages (macOS): `brew install openclaw`
- Test with: `openclaw --version`

## Setup

```bash
cd /Users/faizan/agent-bridge/workspace

# Install Python dependencies
python3 -m pip install -r requirements-test.txt
# For UI (macOS only):
python3 -m pip install rumps pync
```

## Verification Sequence

Run the automated verification script:

```bash
bash scripts/verify_poller.sh
```

This performs:
1. Generates demo memory (`memory_demo.json`)
2. Validates schema with `comprehensive_validator.py`
3. Checks OpenClaw CLI availability
4. Tests JSON output of `openclaw sessions`
5. Verifies rumps import (macOS only)

## Launch the UI (macOS)

```bash
python3 -m rumps_app.main
```

The menu bar app displays the latest polled task with emotion icon.

## Send a Test Message

First, find your OpenClaw session ID:

```bash
openclaw sessions --json
```

Then send a message:

```bash
bash scripts/send_test_message.sh <session_id> "Hello from Hermes!"
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `openclaw: command not found` | Install OpenClaw or add to PATH |
| `ImportError: No module named 'rumps'` | `pip install rumps pync` (macOS only) |
| Validator fails: "empty title" | Ensure you ran latest poller with `--use-demo` flag |
| Sessions command hangs | Check OpenClaw is running; may need to restart agent |
| UI not appearing | Ensure you're on macOS with GUI session |

## File Reference

- `things_sentiment_poller.py` — main poller with demo mode (`--demo`, `--use-demo`)
- `comprehensive_validator.py` — validates memory schema and sentiment mapping
- `memory.json` / `memory_demo.json` — poller output consumed by UI
- `scripts/verify_poller.sh` — full verification pipeline
- `scripts/send_test_message.sh` — OpenClaw agent message wrapper
- `rumps_app/main.py` — macOS menu bar UI entrypoint

## Technical Notes

- MCP integration fails due to `structuredContent` parsing issues; direct CLI is used instead
- Poller runs independently; OpenClaw is only for agent messaging
- Memory schema is JSON with `last_poll`, `last_task_id`, and `tasks[]` array
- Emotions: `neutral`, `stress`, `motivation`, `anxiety`, `excitement`, etc.
