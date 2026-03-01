# =============================================================================
# XtraSkill Backend - Multi-stage Docker Build
# =============================================================================
# Stage 1: Builder - Install dependencies
# Stage 2: Runner - Minimal production image
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS builder

# Install uv for fast dependency management
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY requirements.txt .

# Install dependencies into isolated environment
RUN uv pip install --system --no-cache -r requirements.txt

# -----------------------------------------------------------------------------
# Stage 2: Runner
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS runner

# Security: Run as non-root user
RUN groupadd -r xtra && useradd -r -g xtra xtra

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Required for cryptography
    libffi-dev \
    libssl-dev \
    # Required for some document parsing
    libmagic1 \
    # Required for WeasyPrint
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .
COPY main.py .

# Create data directory
RUN mkdir -p /app/data /app/logs && chown -R xtra:xtra /app

# Switch to non-root user
USER xtra

# Expose port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run with gunicorn
CMD ["gunicorn", "main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "120"]
