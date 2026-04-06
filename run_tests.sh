#!/bin/bash
# Test runner script for things_sentiment_poller

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}[*] Running pytest for things_sentiment_poller...${NC}"

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}[-] pytest not found. Install with: pip install pytest${NC}"
    exit 1
fi

# Run tests with verbose output
pytest tests/ -v --tb=short

# Check exit code
if [ $? -eq 0 ]; then
    echo -e "${GREEN}[+] All tests passed!${NC}"
else
    echo -e "${RED}[-] Some tests failed. See output above.${NC}"
    exit 1
fi