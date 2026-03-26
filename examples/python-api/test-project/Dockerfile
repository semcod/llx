# syntax=docker/dockerfile:1.4

# ---------- Builder stage ----------
FROM python:3.11-slim AS builder

# Install build dependencies (if any) – keep slim
RUN apt-get update && apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt# Copy application source
COPY . .

# ---------- Runtime stage ----------
FROM python:3.11-slim

# Environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
# Copy application codeCOPY --from=builder /app /app

# Create non‑root user
RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser

USER appuser

# Expose the API port
EXPOSE 8000

# Healthcheck endpoint (adjust path if needed)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]