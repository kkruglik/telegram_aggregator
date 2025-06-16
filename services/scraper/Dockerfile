FROM python:3.13-slim as builder

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && \
   curl -LsSf https://astral.sh/uv/install.sh | sh && \
   apt-get clean && \
   rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV PATH="/root/.local/bin:$PATH" \
   UV_COMPILE_BYTECODE=1 \
   UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
   uv sync --frozen

# Production stage
FROM python:3.13-slim

# Create non-root user with explicit UID/GID
RUN groupadd -g 1000 appuser && \
   useradd -u 1000 -g appuser -m -s /bin/bash appuser

ENV PYTHONDONTWRITEBYTECODE=1 \
   PYTHONUNBUFFERED=1 \
   PYTHONPATH=/app \
   PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Copy virtual environment from builder with proper ownership
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Copy application code with proper ownership
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser config/ ./config/

# Create logs directory with proper permissions
RUN mkdir -p logs && chown appuser:appuser logs

# Switch to non-root user
USER appuser

EXPOSE 8000

CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]