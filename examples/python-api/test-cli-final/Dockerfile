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

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Stage 2: Production
FROM python:3.11-slim

# Set working directory to /app
WORKDIR /app

# Copy dependencies from build stage
COPY --from=build /app/requirements.txt.

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --from=build /app.

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup appuser
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=10s --timeout=3s --retries=3 CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--workers", "4"]

# Run command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--workers", "4"]
This Dockerfile uses a multi-stage build to optimize the production image size. The first stage (`build`) is used to install dependencies and copy the application code, while the second stage (`production`) is used to install the dependencies again and copy the application code, but this time with the non-root user and optimized for production.

Note that you'll need to create a `requirements.txt` file in the root of your project with the dependencies required by your FastAPI app.