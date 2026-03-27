# Stage 1: Build the application
FROM python:3.11-slim AS build

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Build the application
RUN pip install --no-cache-dir -e .

# Stage 2: Create the production image
FROM python:3.11-slim

# Set the working directory to /app
WORKDIR /app

# Copy the application code from the build stage
COPY --from=build /app .

# Set the non-root user
USER 1001

# Expose the port
EXPOSE 8000

# Set the health check
HEALTHCHECK --interval=5m --timeout=3s --retries=3 CMD ["curl", "-f", "http://localhost:8000/healthcheck"]

# Run the command when the container starts
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--workers", "4"]