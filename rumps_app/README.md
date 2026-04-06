# Hermes Rumps UI Layer

macOS menu bar application for Hermes/OpenClaw with real-time sentiment visualization and dashboard.

## Features

- **Menu bar icon**: Color-coded based on sentiment intensity (pulsing animation)
- **Latest Appreciation**: Shows newest sentiment message in menu
- **Dashboard window**: Aggregated stats, recent events, OpenClaw status
- **Notifications**: Native macOS alerts for sentiment events and Things completions
- **Memory persistence**: All data stored in `memory.json`
- **OpenClaw integration**: Polls for new messages and session status

## Installation

```bash
cd /Users/faizan/agent-bridge/workspace/rumps_app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running

```bash
python main.py
```

The app will appear in your menu bar as "Hermes".

## Coordination with Clawdiya

- UI sends sentiment events to `memory.json` which the polling loop detects
- Dashboard reads from `memory.json` and OpenClaw CLI
- Real-time icon updates based on latest sentiment intensity
- `Test Notification` menu item verifies pync integration

## Integration Points

- **OpenClaw CLI**: `openclaw sessions --json`, `openclaw messages read`
- **Memory file**: `workspace/memory.json`
- **Things 3**: Clawdiya will hook into `things` CLI and add entries to memory.json
- **Notifications**: `pync.notify()` for native alerts

## Next Steps

1. Test basic app startup and menu display
2. Verify memory.json gets created and updated
3. Confirm OpenClaw sessions are detected
4. Clawdiya: Wire Things integration and sentiment events to memory.json
5. Together: End-to-end test with real sentiment data
