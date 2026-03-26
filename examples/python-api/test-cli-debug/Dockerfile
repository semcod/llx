Here is a multi-stage Dockerfile for a FastAPI app:
# Stage 1: Build stage
FROM python:3.11-slim AS build

# Set working directory to /app
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Build the application
RUN python -m pip install --no-cache-dir --upgrade pip
RUN python -m pip install --no-cache-dir -r requirements.txt
RUN python setup.py install

# Stage 2: Production stage
FROM python:3.11-slim

# Set working directory to /app
WORKDIR /app

# Copy the application code from the build stage
COPY --from=build /app .

# Expose the port
EXPOSE 8000

# Set environment variables
ENV NAME World
ENV DESCRIPTION My FastAPI App

# Set health check
HEALTHCHECK --interval=10s --timeout=5s --retries=3 CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--workers", "4"]

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--workers", "4"]

# Set non-root user
USER 1001:1001
This Dockerfile uses a multi-stage build to optimize the build process. The first stage (`build`) is used to install dependencies and build the application, while the second stage (`production`) is used to create the final production image.

Here's a brief explanation of each section:

*   The first stage (`build`) installs the dependencies and builds the application. It uses the `python:3.11-slim` base image and sets the working directory to `/app`.
*   The second stage (`production`) uses the same base image as the first stage but creates a new image with the application code copied from the first stage. It exposes port 8000, sets environment variables, and defines a health check using `uvicorn`.
*   The `USER` instruction sets the non-root user to `1001:1001` to run the application with a non-root user.

Note that you'll need to replace `main:app` with the actual module and function name of your FastAPI app.