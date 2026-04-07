# OpenClaw Things Sentiment Integration

**Deployed to:** https://github.com/faizanxg-AI/openclaw-things-sentiment

![Verification](https://github.com/faizanxg-AI/openclaw-things-sentiment/actions/workflows/verify.yml/badge.svg)


A robust integration between Things task manager sentiment analysis and OpenClaw agent-to-agent communication. This system polls tasks from Things, analyzes emotional tone, and shares insights via OpenClaw's agent messaging layer.

## Quick Overview

| Component | Description |
|-----------|-------------|
| `things_sentiment_poller.py` | Main poller - collects tasks, determines emotion, writes `memory.json` |
| `comprehensive_validator.py` | Schema and business logic validation for poller output |
| `rumps_app/` | macOS menu bar UI for live sentiment display |
| `scripts/` | Automation: verification, test messaging |
| `Makefile` | Convenient targets for all common tasks |
| `Dockerfile` | Containerized verification for CI |

## One-Minute Setup

```bash
# 1. Install dependencies
pip install -r requirements-test.txt

# 2. Verify everything works
make verify

# 3. Generate demo data (or run real poller)
make demo

# 4. Launch UI (macOS only)
make ui
```

See [QUICKSTART.md](QUICKSTART.md) for detailed setup, troubleshooting, and platform-specific notes.

## Quick Start (Smart Script)

For guided setup, run the smart quick-start script that auto-detects your environment:

```bash
make quickstart
# or
bash quickstart.sh
```

It will check for macOS/Linux, Docker, Python 3.11, and OpenClaw CLI, then recommend the best deployment method (native UI, Docker container, or headless Python). Optionally auto-execute setup.

### Pre-flight Validation

Before deploying, run the pre-flight check to catch configuration issues:

```bash
make preflight
# or
python3 scripts/preflight_check.py
```

This validates: Python 3.11, virtual environment, dependencies, OpenClaw CLI, configuration files, memory file, file permissions, Docker, systemd, and environment variables. All checks must pass for reliable operation.

---

## Architecture Highlights

- **Two-Layer Design**: Poller runs independently; OpenClaw communication via direct CLI (MCP bypass due to `structuredContent` parsing limitations)
- **Memory Schema**: Simple JSON format with tasks containing `emotion`, `project`, `tags`, etc.
- **Resilient**: Demo mode for testing, schema validation, permission system integration tested
- **Production-Ready**: Full CI pipeline, Docker support, Makefile automation, comprehensive documentation

## Common Commands

```bash
make verify        # Full verification (demo + validate + CLI checks)
make demo          # Generate demo memory file with 15 entries
make validate      # Run validator on memory.json
make ui            # Launch menu bar app (macOS)
make preflight     # Run pre-flight validation (dependencies, config, permissions)
make healthcheck   # Check polling service health (returns 0 if healthy)
make send-test SESSION_ID=<id>  # Send test message via OpenClaw
make docker-run    # Containerized verification (CI/isolated)
```

## Project Structure

```
.
├── polling_service.py            # Production daemon with scheduling & health checks
├── automation/
│   └── rule_engine.py           # YAML-based notification rule engine
├── comprehensive_validator.py   # Schema + emotion validation
├── rumps_app/                   # macOS menu bar UI
├── tests/                       # Full test suite (62 tests)
├── config/
│   ├── polling_service.yaml     # Polling interval, startup delay, task limits
│   └── automation_rules.yaml    # Sentiment/category/intensity rules with cooldowns
├── scripts/
│   ├── start_polling.sh         # Production launcher with venv detection
│   ├── healthcheck.py           # Health check script (returns 0 if service healthy)
│   ├── preflight_check.py       # Pre-flight validation (dependencies, config, permissions)
│   ├── verify_poller.sh         # Automated verification pipeline
│   └── send_test_message.sh     # Test messaging
├── deploy/
│   └── systemd/
│       └── things-sentiment-poller.service  # Systemd unit file for Linux
├── .github/
│   └── workflows/
│       ├── docker-build.yml     # Multi-arch Docker builds + SBOM
│       └── verify.yml           # CI pipeline (tests)
├── Makefile                     # Task automation (verify, demo, ui, poll-*, healthcheck, docker-*)
├── Dockerfile                   # Container with health checks
├── quickstart.sh                # ⭐ Smart environment detection & guided setup
├── setup.sh                     # macOS UI setup
├── README.md                    # Project overview + CI badge + deployment guide
├── FINAL_SUMMARY.md            # Comprehensive production recap
├── DEPLOYMENT_STATUS.md        # This file - current status
└── requirements-test.txt        # Test dependencies
```

## Compatibility

- **OS**: macOS (full UI) or Linux (headless verification, Docker)
- **Python**: 3.11+
- **OpenClaw**: CLI must be installed and in PATH (`brew install openclaw` on macOS)
- **UI dependencies**: `rumps`, `pync` (macOS only)

## OpenClaw Auto-Forwarding (Optional)

Set the environment variable `OPENCLAW_SESSION_KEY` to automatically send a summary message to an OpenClaw session after each poller run:

```bash
# Get your active session key (first one)
export OPENCLAW_SESSION_KEY=$(openclaw sessions --json | python3 -c "import sys, json; print(json.load(sys.stdin)['sessions'][0]['key'])")

# Run poller (demo or live)
make demo  # Summary will be sent to the configured session
```

This enables the poller to notify an agent (e.g., Clawdiya) whenever new sentiment data is available without manual intervention.

## Live Polling Service & Automation

For production operation, run the polling service as a daemon that continuously checks for completed tasks and triggers OpenClaw notifications based on sentiment rules.

### Quick Start

1. **Configure automation rules** (optional): Edit `config/automation_rules.yaml`
2. **Set environment variable**: `export OPENCLAW_SESSION_KEY=<your-session-key>`
3. **Start the service**: `make poll-start`

```bash
# Start polling (runs in foreground)
make poll-start

# Or run once for testing
make poll-start ARGS="--once"

# Check status file
make poll-status

# Stop the service
make poll-stop
```

**Configuration:** See `config/polling_service.yaml` to adjust:
- Poll interval (default 30 minutes)
- Demo mode (use synthetic tasks for testing)
- OpenClaw summary template
- Automation rule processing

### OpenClaw Automation Rules

Define rule-based notifications in `config/automation_rules.yaml`:

```yaml
rules:
  - name: "High Frustration Alert"
    emotion: "frustration"
    min_intensity: 0.8
    message_template: "Task completed with high frustration: {title}"
    session_target: "main"
    enabled: true
```

Rules trigger when sentiment entries match emotion, category, and intensity thresholds. Cooldowns prevent spam.

### Health Checks & Monitoring

Polling service writes its status to `polling_status.json` after each cycle. Check health with:

```bash
make healthcheck               # Run health check script (returns 0 if healthy)
make poll-status               # View full status JSON
```

External monitoring (systemd, Monit, Nagios) can watch the status file for freshness and expected values.

### Linux Systemd Deployment

For production servers, use the provided systemd unit file:

```bash
# 1. Copy unit file to user systemd directory
mkdir -p ~/.config/systemd/user
cp deploy/systemd/things-sentiment-poller.service ~/.config/systemd/user/

# 2. Edit the unit file to set correct WorkingDirectory path

# 3. Reload systemd and enable/start the service
systemctl --user daemon-reload
systemctl --user enable --now things-sentiment-poller

# 4. Check status
systemctl --user status things-sentiment-poller
journalctl --user -u things-sentiment-poller -f
```

The service will start automatically on login and restart on failures.

---

## Docker Deployment (Recommended for Linux/CI)

The project includes full Docker support for portable, multi-architecture deployment:

```bash
# Quick verification in container
make docker-run

# Persistent service with docker-compose
make docker-up    # Start in background
make docker-logs  # View logs
make docker-stop  # Stop service
```

**Docker features:**
- Multi-arch builds (amd64, arm64)
- Persistent volumes for `data/` (memory.json) and `config/`
- Health checks and restart policies
- Ideal for CI/CD and headless Linux servers

See `docker-compose.yml` for configuration options

## Pre-built Docker Images

Docker images are automatically built and published to GitHub Container Registry (GHCR) on every push to `main`:

```bash
# Pull the latest multi-architecture image
docker pull ghcr.io/faizanxg-ai/openclaw-things-sentiment:latest

# Run directly without building
docker run --rm ghcr.io/faizanxg-ai/openclaw-things-sentiment:latest

# Or with docker-compose using the pre-built image
# In docker-compose.yml, replace `build:` with `image: ghcr.io/faizanxg-ai/openclaw-things-sentiment:latest`
```

**Available tags:**
- `latest` - Most recent build from main branch
- `main-<sha>` - Specific commit (e.g., `main-a3159ea`)
- `v*` - Semantic version tags (when you create releases)
- `amd64`, `arm64` - Multi-architecture support built-in

Images are built for both `linux/amd64` and `linux/arm64` (Raspberry Pi, Apple Silicon) and include a Software Bill of Materials (SBOM) for security auditing.

### Cross-Platform Web Dashboard

For a browser-based UI available on any OS, use the Flask dashboard:

```bash
# Ensure data exists (run poller or generate demo)
make demo
# Launch dashboard
make dashboard
# Open http://localhost:8000 in your browser
```

The dashboard displays:
- Total sentiment entries and dominant emotions/categories
- Latest entry details with timestamp
- Table of recent entries (auto-refresh every 30s)

Dashboard app: `dashboard/app.py` (Flask, port 8000). Expose port 8000 in Docker if running containerized.

## Verification Status

Production deployment fully verified and ready:

✅ All 62 tests passing (4 skipped for future enhancements)  \
✅ Core production files: polling_service.py, rule_engine.py, configs  \
✅ Make targets: verify, verify-production, poll-*, healthcheck, quickstart, dashboard  \
✅ Health check script and status JSON tracking  \
✅ Systemd service file for Linux servers  \
✅ Docker multi-arch builds (amd64/arm64) with CI/CD  \
✅ Comprehensive documentation: README, FINAL_SUMMARY.md, DEPLOYMENT_STATUS.md  \
✅ OpenClaw integration tested with fallback strategies  \
✅ YAML configuration validated (polling + automation rules)  \

Run `make verify-production` for a full 23-point deployment check, or see `DEPLOYMENT_STATUS.md` for the complete verification report.

## Next Steps

**For first-time users:** Run `make quickstart` for intelligent environment detection and guided setup.

**For production deployment:**
1. Run `make verify-production` to confirm all components are ready
2. Configure your `OPENCLAW_SESSION_KEY` environment variable
3. Choose your deployment:
   - macOS UI: `bash setup.sh && make ui`
   - Live polling: `make poll-start`
   - Docker: `docker pull ghcr.io/faizanxg-ai/openclaw-things-sentiment:latest`
   - Systemd (Linux): See `deploy/systemd/` directory
4. Customize automation rules in `config/automation_rules.yaml` as needed

**For development/testing:** Use `make verify`, `make demo`, and `make send-test SESSION_ID=<id>`.

## License

Project-specific license - see repository details.

---

**Note**: This integration uses OpenClaw's direct CLI as a fallback due to MCP `structuredContent` parsing incompatibility with generic clients. See [COMMUNICATION.md](COMMUNICATION.md) for technical details.