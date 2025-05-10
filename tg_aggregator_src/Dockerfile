FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates

ADD https://astral.sh/uv/install.sh /uv-installer.sh

RUN sh /uv-installer.sh && rm /uv-installer.sh

ENV PATH="/root/.local/bin/:$PATH"

COPY pyproject.toml uv.lock ./
COPY config/aggregator ./config/aggregator
COPY tg_aggregator_src/ ./tg_aggregator_src/

RUN uv sync --frozen

RUN mkdir -p logs

CMD ["uv", "run", "python", "-m", "tg_aggregator_src.tg_aggregator.main"]
