import logging
import os

import uvicorn
from fastapi import FastAPI, HTTPException

from .models import ChannelRequest, ChannelMessages, ChannelIDRequest, ChannelIDResponse
from .scraper import TelegramScraperQueue
from .config import API_ID, API_HASH

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
)
logger = logging.getLogger('telegram_scraper_service')

app = FastAPI(
    title="Telegram Scraper Service",
    description="Microservice for scraping Telegram channels",
    version="1.0.0",
)

# Create a singleton queue instance
telegram_queue = TelegramScraperQueue(API_ID, API_HASH, 'telegram_scraper')


@app.on_event("startup")
async def startup_event():
    """Start the Telegram client queue on startup"""
    await telegram_queue.start()


@app.post("/messages", response_model=ChannelMessages)
async def get_messages(request: ChannelRequest):
    """Get today's messages from a Telegram channel"""
    try:
        result = await telegram_queue.get_today_messages(request.channel_id)
        return result
    except Exception as e:
        logger.error(f"Error getting messages: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")


@app.post("/channel_id", response_model=ChannelIDResponse)
async def get_channel_id(request: ChannelIDRequest):
    """Get the channel ID for a given channel username or link"""
    try:
        channel_id, username = await telegram_queue.get_channel_id(request.channel)
        return ChannelIDResponse(channel_id=channel_id, username=username)
    except Exception as e:
        logger.error(f"Error getting channel ID: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get channel ID: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "telegram-scraper"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
