# --- Stage 1: The Builder ---
# This stage installs all tools and dependencies, and consolidates
# all necessary application files into a single /app directory.
FROM python:3.12-slim AS builder

# 1. Install build tools
WORKDIR /tmp/build
RUN pip install uv

# 2. Install Python dependencies into the global site-packages
COPY pyproject.toml uv.lock ./
RUN uv pip install --system --no-cache -r pyproject.toml

# 3. Consolidate application code and data into a clean /app directory
WORKDIR /app
COPY game_data_parser ./game_data_parser
COPY src ./src
COPY web ./web
COPY game_data.cache .


# --- Stage 2: The Final Production Image ---
# This stage starts from a fresh base image and copies only the
# necessary, pre-prepared artifacts from the builder stage.
FROM python:3.12-slim

# Create a non-root user for better security
RUN useradd --create-home appuser
WORKDIR /home/appuser/app

# Copy necessary artifacts from the builder stage:
# 1. The installed Python packages
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
# 2. The executable scripts (like uvicorn, fastapi)
COPY --from=builder /usr/local/bin /usr/local/bin
# 3. The entire, consolidated application code and data
COPY --from=builder /app .

# Set correct ownership for the entire application directory, then switch user
RUN chown -R appuser:appuser /home/appuser/app
USER appuser

# Set the command to run the FastAPI application
CMD ["uvicorn", "web.backend.main:app", "--host", "0.0.0.0", "--port", "8666"]