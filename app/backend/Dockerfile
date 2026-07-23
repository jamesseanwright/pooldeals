# Stage 1: Build dependencies
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS uv
WORKDIR /build

# Copy only pyproject.toml and uv.lock for reproducible builds
COPY app/backend/pyproject.toml app/backend/uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-install-project --no-dev

# Stage 2: Build the application
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /build

# Copy virtual environment from previous stage
COPY --from=uv /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application source
COPY app/backend/ .

# Build the package (if needed) — not required for FastAPI app run directly
# RUN uv build

# Stage 3: Runtime
FROM ghcr.io/astral-shuv:python3.12-bookworm-slim AS runtime

WORKDIR /app

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=appuser:appuser app/backend/ .

# Switch to non-root user
USER appuser

# Expose the FastAPI port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "fastapi", "run", "main.py", "--host", "0.0.0.0", "--port", "8000"]
