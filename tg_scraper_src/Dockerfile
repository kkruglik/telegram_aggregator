FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

RUN pip install --upgrade pip && \
    pip install fastapi==0.115.1 uvicorn==0.34.2 telethon==1.39.0 python-dotenv==1.1.0 google-cloud-secret-manager==2.23.3 pyyaml==6.0.2

COPY tg_scraper_src/ ./tg_scraper_src/
COPY config/ ./config/

RUN mkdir -p logs

EXPOSE 8000

CMD ["uvicorn", "tg_scraper_src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]