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

## Architecture Highlights

- **Two-Layer Design**: Poller runs independently; OpenClaw communication via direct CLI (MCP bypass due to `structuredContent` parsing limitations)
- **Memory Schema**: Simple JSON format with tasks containing `emotion`, `project`, `tags`, etc.
- **Resilient**: Demo mode for testing, schema validation, permission system integration tested
- **Production-Ready**: Full CI pipeline, Docker support, Makefile automation, comprehensive documentation

## Common Commands

```bash
make verify      # Full verification (demo + validate + CLI checks)
make demo        # Generate demo memory file with 15 entries
make validate    # Run validator on memory.json
make ui          # Launch menu bar app (macOS)
make send-test SESSION_ID=<id>  # Send test message via OpenClaw
make docker-run  # Containerized verification (CI/isolated)
```

## Project Structure

```
.
├── things_sentiment_poller.py   # Main poller with demo mode
├── comprehensive_validator.py   # Schema + emotion validator
├── rumps_app/                   # macOS UI
│   └── main.py
├── scripts/
│   ├── verify_poller.sh         # Automated verification pipeline
│   └── send_test_message.sh     # Test message sender
├── .github/workflows/verify.yml # CI pipeline
├── Makefile                     # Task automation
├── Dockerfile                   # Container verification
├── COMMUNICATION.md             # Architecture deep-dive
├── QUICKSTART.md                # End-user guide
└── README.md                    # This file
```

## Compatibility

- **OS**: macOS (full UI) or Linux (headless verification)
- **Python**: 3.11+
- **OpenClaw**: CLI must be installed and in PATH (`brew install openclaw` on macOS)
- **UI dependencies**: `rumps`, `pync` (macOS only)

## Verification Status

All components verified and locked:

✅ Demo generation creates 15 entries including edge cases  
✅ Validator passes on generated memory  
✅ OpenClaw CLI available and JSON output working  
✅ Permission system properly blocks unapproved exec  
✅ Scripts executable, Makefile targets complete  
✅ Git repository initialized, CI workflow added  

See `FINAL_STATUS.md` for full verification report.

## Next Steps

1. Run `make verify` to confirm your environment
2. Copy `memory_demo.json` to `memory.json` (or run real poller)
3. Launch UI with `make ui` (macOS) or integrate with your workflow
4. Use `make send-test` to validate OpenClaw communication

## License

Project-specific license - see repository details.

---

**Note**: This integration uses OpenClaw's direct CLI as a fallback due to MCP `structuredContent` parsing incompatibility with generic clients. See [COMMUNICATION.md](COMMUNICATION.md) for technical details.