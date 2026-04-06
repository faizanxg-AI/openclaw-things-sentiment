.PHONY: help verify demo validate ui test clean docker-build

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

verify: ## Run full verification sequence (demo + validate + CLI checks)
	@bash scripts/verify_poller.sh

demo: ## Generate demo memory file
	@python3 things_sentiment_poller.py --demo --demo-count 15 --use-demo

validate: ## Run comprehensive validator on memory.json (or memory_demo.json)
	@python3 comprehensive_validator.py

test: verify ## Alias for verify

ui: ## Launch rumps UI (macOS only)
	@python3 -m rumps_app.main

send-test: ## Send test message (requires SESSION_ID env var)
	@if [ -z "$(SESSION_ID)" ]; then echo "Usage: make send-test SESSION_ID=<id>"; exit 1; fi
	@bash scripts/send_test_message.sh "$(SESSION_ID)" "Test from make"

clean: ## Remove generated files
	@rm -f memory.json memory_demo.json
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

docker-build: ## Build verification container
	docker build -t openclaw-poller-verify .

docker-run: docker-build ## Build and run container verification
	docker run --rm openclaw-poller-verify
