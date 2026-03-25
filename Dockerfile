# Multi-stage build for llx
FROM python:3.11-slim as builder

# Set build arguments
ARG BUILD_DATE
ARG VERSION
ARG VCS_REF

# Labels
LABEL maintainer="Tom Sapletta <tom@sapletta.org>"
LABEL org.label-schema.build-date=$BUILD_DATE
LABEL org.label-schema.name="llx"
LABEL org.label-schema.description="Intelligent LLM model router driven by real code metrics"
LABEL org.label-schema.url="https://github.com/wronai/llx"
LABEL org.label-schema.vcs-ref=$VCS_REF
LABEL org.label-schema.vcs-url="https://github.com/wronai/llx"
LABEL org.label-schema.vendor="Tom Sapletta"
LABEL org.label-schema.version=$VERSION

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    jq \
    netcat-openbsd \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r llx && useradd -r -g llx llx

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
COPY requirements-dev.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install -r requirements-dev.txt

# Copy application code
COPY . .

# Install llx in development mode
RUN pip install -e .

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/llx/.local/bin:$PATH"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    netcat-openbsd \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# Create app user
RUN groupadd -r llx && useradd -r -g llx llx

# Create directories
RUN mkdir -p /app/logs /app/cache /app/data && \
    chown -R llx:llx /app

# Copy from builder stage
COPY --from=builder --chown=llx:llx /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder --chown=llx:llx /usr/local/bin /usr/local/bin
COPY --from=builder --chown=llx:llx /app /app

# Switch to app user
USER llx

# Set work directory
WORKDIR /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:4000/health || exit 1

# Expose port
EXPOSE 4000

# Default command
CMD ["python", "-m", "llx", "proxy", "start"]
