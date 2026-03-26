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
RUN groupadd -r app && useradd -r -g app app

# Set environment variables
ENV APP_NAME My Project
ENV APP_VERSION 1.0

# Expose port
EXPOSE 8000

# Health checks
HEALTHCHECK --interval=10s --timeout=3s --retries=3 CMD ["curl", "-f", "http://localhost:8000/healthcheck"]

# Run the application
CMD ["gunicorn", "main:app", "--workers", "3", "--bind", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-"]
This Dockerfile uses a multi-stage build to optimize the build process. The first stage (`build`) is used to install dependencies and build the application, while the second stage (`production`) is used to create the final production image.

The `production` stage sets up a non-root user, exposes port 8000, and defines health checks using `curl`. The `CMD` instruction runs the application using `gunicorn`.

Note that you'll need to create a `requirements.txt` file in the root of your project with the dependencies required by your FastAPI app.