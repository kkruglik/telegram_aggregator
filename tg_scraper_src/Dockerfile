FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

RUN pip install --upgrade pip && \
    pip install fastapi uvicorn telethon python-dotenv

COPY tg_scraper_src/ ./tg_scraper_src/
COPY telegram_scraper.session ./telegram_scraper.session


RUN mkdir -p logs

EXPOSE 8000

CMD ["uvicorn", "tg_scraper_src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]