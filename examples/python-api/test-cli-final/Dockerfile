Here is a multi-stage Dockerfile for a FastAPI app:

# Stage 1: Build
FROM python:3.11-slim AS build

# Set working directory to /app
WORKDIR /app

# Copy requirements file
COPY requirements.txt.

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY..

# Build the application
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir black flake8 && \
    black. && \
    flake8.

# Stage 2: Production
FROM python:3.11-slim

# Set working directory to /app
WORKDIR /app

# Copy the application code from the build stage
COPY --from=build /app.

# Set non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup appuser && \
    chown -R appuser:appgroup /app

# Set environment variables
ENV FASTAPI_HOST=0.0.0.0
ENV FASTAPI_PORT=8000

# Health checks
HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
    CMD ["curl", "-f", "http://localhost:8000/health"]

# Expose port
EXPOSE 8000

# Run the application
CMD ["gunicorn", "main:app", "--workers", "3", "--bind", "0.0.0.0:8000"]

This Dockerfile uses a multi-stage build to optimize the production image size. The `build` stage installs dependencies and builds the application, while the `production` stage copies the application code and sets up the non-root user. The `HEALTHCHECK` directive is used to define a health check for the application. The `CMD` directive is used to specify the command to run when the container is started.