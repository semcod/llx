# Multi-stage build for llx
FROM python:3.11-slim AS builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=0 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy pyproject.toml and requirements for caching
COPY pyproject.toml .
COPY requirements.txt .

# Install dependencies with cache mount
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code
COPY . .

# Install llx (without dev deps for production-ready builder)
RUN pip install .

# Production stage
FROM python:3.11-slim AS production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/llx/.local/bin:$PATH"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# Create app user
RUN groupadd -r llx && useradd -r -g llx llx

# Create directories
RUN mkdir -p /app/logs /app/cache /app/data && \
    chown -R llx:llx /app

# Copy from builder stage - only what's necessary
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder --chown=llx:llx /app/llx /app/llx
COPY --from=builder --chown=llx:llx /app/pyproject.toml /app/pyproject.toml

# Switch to app user
USER llx
WORKDIR /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:4000/health || exit 1

EXPOSE 4000

# Default command
CMD ["python", "-m", "llx", "proxy", "start"]
