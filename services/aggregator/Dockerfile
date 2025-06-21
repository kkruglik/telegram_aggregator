FROM python:3.13-slim as builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV PATH="/root/.local/bin:$PATH" \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_CACHE_DIR=/tmp/uv-cache

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/tmp/uv-cache \
    uv sync --frozen --no-dev

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

COPY config/ ./config/
COPY src/ ./src/
COPY migrations/ ./migrations/

RUN mkdir -p logs

EXPOSE 8000

CMD ["python", "-m", "src.app.main"]