.PHONY: help verify demo validate ui test clean docker-build docker-run docker-stop docker-logs

# Auto-detect virtual environment - use .venv if present, else system python3.11
PYTHON := python3.11
ifeq ($(wildcard .venv/bin/python),)
else
    PYTHON := .venv/bin/python
endif

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

verify: ## Run full verification sequence (demo + validate + CLI checks)
	@bash scripts/verify_poller.sh

demo: ## Generate demo memory file
	@$(PYTHON) things_sentiment_poller.py --demo --demo-count 15 --use-demo

validate: ## Run comprehensive validator on memory.json (or memory_demo.json)
	@$(PYTHON) comprehensive_validator.py

test: verify ## Alias for verify

ui: ## Launch rumps UI (macOS only)
	@$(PYTHON) -m rumps_app.main

send-test: ## Send test message (requires SESSION_ID env var)
	@if [ -z "$(SESSION_ID)" ]; then echo "Usage: make send-test SESSION_ID=<id>"; exit 1; fi
	@bash scripts/send_test_message.sh "$(SESSION_ID)" "Test from make"

clean: ## Remove generated files
	@rm -f memory.json memory_demo.json
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

docker-build: ## Build multi-arch container image
	docker buildx build --platform linux/amd64,linux/arm64 -t openclaw-things-sentiment:latest --load .

docker-run: docker-build ## Build and run container (verification)
	docker-compose run --rm openclaw-things-sentiment

docker-up: ## Build and run container in background (persistent)
	docker-compose up -d

docker-stop: ## Stop running container
	docker-compose down

docker-logs: ## View container logs
	docker-compose logs -f

docker-prune: ## Clean Docker resources (images, containers, volumes)
	docker system prune -af --volumes

quickstart: ## Smart environment detection and guided setup
	@echo "Running quick start wizard..."
	bash quickstart.sh
