FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates

ADD https://astral.sh/uv/install.sh /uv-installer.sh

RUN sh /uv-installer.sh && rm /uv-installer.sh

ENV PATH="/root/.local/bin/:$PATH"

COPY pyproject.toml uv.lock ./
COPY config/ ./config/
COPY src/ ./src/

RUN uv sync --frozen

RUN mkdir -p logs

CMD ["uv", "run", "python", "-m", "src.app.main"]
