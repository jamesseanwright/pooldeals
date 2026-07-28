# Stage 1: Build stage using uv
FROM ghcr.io/astral-sh/uv:python3.12-bookworm AS builder

WORKDIR /build

# Copy project files
COPY src/ src/
COPY pyproject.toml pyproject.toml
COPY uv.lock uv.lock
COPY README.md README.md

# Install dependencies using uv
RUN uv sync --frozen --no-install-workspace --no-dev

# Stage 2: Final slim runtime image
FROM python:3.12-slim-bookworm

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create non-root user
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash appuser

# Copy installed dependencies from builder stage
COPY --from=builder /root/.local /home/appuser/.local

# Ensure binaries are in PATH for non-root user
ENV PATH=/home/appuser/.local/bin:$PATH

# Copy application source
COPY src/ src/

# Expose the default FastAPI port
EXPOSE 8000

# Switch to non-root user
USER appuser

# Run the application using fastapi CLI (with full path to ensure CLI is found)
CMD ["/home/appuser/.local/bin/fastapi", "run", "src/main.py", "--host", "0.0.0.0", "--port", "8000"]
