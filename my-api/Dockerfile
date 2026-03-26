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

# Build the app
RUN python -m pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir black isort

# Stage 2: Production stage
FROM python:3.11-slim

# Set working directory to /app
WORKDIR /app

# Copy the application code from the build stage
COPY --from=build /app .

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set non-root user
USER 1001:1001

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=3 CMD ["python", "-c", "import uvicorn; uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=False, debug=False)"]

# Expose port 8000
EXPOSE 8000

# Run the command to start the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "False", "--debug", "False"]
This Dockerfile uses a multi-stage build to optimize the build process. The first stage (`build`) is used to install dependencies and build the application, while the second stage (`production`) is used to create the final production image.

Here's a brief explanation of the Dockerfile:

* The first stage (`build`) installs dependencies and builds the application using `pip`.
* The second stage (`production`) copies the application code from the `build` stage and sets environment variables for optimization.
* The `HEALTHCHECK` instruction is used to define a health check for the container. In this case, it runs the FastAPI app using `uvicorn` and checks its health every 10 seconds.
* The `USER` instruction sets the non-root user for the container.
* The `EXPOSE` instruction exposes port 8000 for the container.
* The `CMD` instruction sets the default command to start the app using `uvicorn`.

Note that you'll need to create a `requirements.txt` file in the root of your project with the dependencies required by your FastAPI app.