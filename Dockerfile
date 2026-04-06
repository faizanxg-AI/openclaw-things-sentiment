# Multi-arch Dockerfile for OpenClaw Things Sentiment Integration
# Supports: linux/amd64, linux/arm64

FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY requirements-test.txt .
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-test.txt

# Runtime image
FROM python:3.11-slim

WORKDIR /app

# Install OpenClaw CLI
RUN curl -fsSL https://raw.githubusercontent.com/openclaw/cli/main/install.sh | sh

# Copy installed dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create data directory for memory.json
RUN mkdir -p data && cp -f memory_demo.json memory.json || true

# Make scripts executable
RUN chmod +x scripts/verify_poller.sh setup.sh

# Expose ports if needed (for future web UI)
# EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python3.11 -c "import sys; sys.exit(0)" || exit 1

# Default command: run verification
CMD ["bash", "scripts/verify_poller.sh"]
