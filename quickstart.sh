#!/usr/bin/env bash

# OpenClaw Things Sentiment - Smart Quick Start
# Auto-detects environment and launches optimal deployment

set -e  # Exit on any error

echo "🔍 OpenClaw Things Sentiment - Quick Start"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Darwin*)
        PLATFORM="macOS"
        ;;
    Linux*)
        PLATFORM="Linux"
        ;;
    *)
        PLATFORM="${OS}"
        ;;
esac

echo -e "${BLUE}Detected Platform:${NC} ${PLATFORM}"
echo ""

# Check for required tools
command -v python3.11 >/dev/null 2>&1 && PYTHON_OK=true || PYTHON_OK=false
command -v docker >/dev/null 2>&1 && DOCKER_OK=true || DOCKER_OK=false
command -v openclaw >/dev/null 2>&1 && OPENCLAW_OK=true || OPENCLAW_OK=false

# Recommendation logic
echo -e "${YELLOW}Environment Check:${NC}"
echo "  Python 3.11:   $([ "$PYTHON_OK" = true ] && echo -e "${GREEN}✓${NC}" || echo -e "${RED}✗${NC}")"
echo "  Docker:        $([ "$DOCKER_OK" = true ] && echo -e "${GREEN}✓${NC}" || echo -e "${RED}✗${NC}")"
echo "  OpenClaw CLI:  $([ "$OPENCLAW_OK" = true ] && echo -e "${GREEN}✓${NC}" || echo -e "${RED}✗${NC}")"
echo ""

# Determine best deployment option
RECOMMENDATION=""

if [ "$PLATFORM" = "macOS" ] && [ "$PYTHON_OK" = true ]; then
    RECOMMENDATION="native-ui"
elif [ "$DOCKER_OK" = true ]; then
    RECOMMENDATION="docker"
elif [ "$PLATFORM" = "Linux" ] && [ "$PYTHON_OK" = true ]; then
    RECOMMENDATION="headless"
else
    RECOMMENDATION="none"
fi

# Show options based on recommendation
case "$RECOMMENDATION" in
    "native-ui")
        echo -e "${GREEN}✓ Recommended: Native macOS UI${NC}"
        echo ""
        echo "You have everything needed for the full macOS menu bar experience:"
        echo "  1. Install dependencies: ${BLUE}bash setup.sh${NC}"
        echo "  2. Launch UI:          ${BLUE}make ui${NC}"
        echo ""
        read -p "Run recommended setup now? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Running setup..."
            bash setup.sh
            echo ""
            echo "Starting UI..."
            make ui || true
        fi
        ;;
    "docker")
        echo -e "${GREEN}✓ Recommended: Docker Container${NC}"
        echo ""
        echo "Docker is available - use the containerized version:"
        echo "  1. Pull pre-built image (optional): ${BLUE}docker pull ghcr.io/faizanxg-ai/openclaw-things-sentiment:latest${NC}"
        echo "  2. Run verification:                ${BLUE}make docker-run${NC}"
        echo "  3. Start persistent service:       ${BLUE}make docker-up${NC}"
        echo ""
        read -p "Run container verification now? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Building and running container..."
            make docker-run
        fi
        ;;
    "headless")
        echo -e "${YELLOW}⚠ Linux detected without Docker${NC}"
        echo ""
        echo "Options:"
        echo "  A) Install Docker for container deployment (recommended)"
        echo "  B) Run in headless mode with native Python"
        echo ""
        read -p "Choose (A/B): " choice
        case "$choice" in
            [Aa]*)
                echo "Please install Docker for your distribution, then re-run this script."
                echo "  Ubuntu: sudo apt install docker.io"
                echo "  Fedora: sudo dnf install docker"
                ;;
            [Bb]*)
                echo "Setting up Python environment..."
                python3.11 -m venv .venv
                source .venv/bin/activate
                pip install -r requirements-test.txt
                echo ""
                echo "Running verification..."
                make verify
                echo ""
                echo "To run the poller (headless):"
                echo "  source .venv/bin/activate"
                echo "  python things_sentiment_poller.py --demo"
                ;;
        esac
        ;;
    "none")
        echo -e "${RED}✗ No suitable deployment method found${NC}"
        echo ""
        echo "Please install one of the following:"
        echo "  • Python 3.11+ (https://www.python.org/downloads/)"
        echo "  • Docker Desktop (https://www.docker.com/products/docker-desktop/)"
        echo ""
        echo "Then re-run this script."
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}✅ Quick start complete!${NC}"
echo ""
echo "Next steps:"
echo "  • Read FINAL_SUMMARY.md for full project overview"
echo "  • Check README.md for detailed documentation"
echo "  • Customize config/config.yaml as needed"
echo ""
echo "Need help? See: https://github.com/faizanxg-AI/openclaw-things-sentiment"
