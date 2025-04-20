import asyncio
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from telethon import TelegramClient

BASE_DIR = Path(__file__).resolve().parents[2]
env_path = BASE_DIR / '.env'
load_dotenv(dotenv_path=env_path)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
)
logger = logging.getLogger('telegram_scraper_service')

# Get credentials from environment variables
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION_NAME = os.getenv("TELEGRAM_SESSION_NAME", "telegram_scraper")


# Models
class Message(BaseModel):
    id: int
    text: str


class ChannelMeta(BaseModel):
    channel_id: int
    date: datetime


class ChannelMessages(BaseModel):
    meta: ChannelMeta
    messages: List[Message]


class ChannelRequest(BaseModel):
    channel_id: int


class ChannelIDRequest(BaseModel):
    channel: str


class ChannelIDResponse(BaseModel):
    channel_id: int
    username: Optional[str] = None


# Create a queue system for the Telegram client
class TelegramScraperQueue:
    def __init__(self, api_id: int, api_hash: str, session_name: str):
        self.client = TelegramClient(session_name, api_id, api_hash)
        self.queue = asyncio.Queue()
        self.running = False
        self.worker_task = None

    async def start(self):
        """Start the queue worker"""
        if self.running:
            return

        await self.client.start()
        self.running = True
        self.worker_task = asyncio.create_task(self._process_queue())
        logger.info("TelegramScraperQueue started")

    async def stop(self):
        """Stop the queue worker"""
        if not self.running:
            return

        self.running = False
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass

        await self.client.disconnect()
        logger.info("TelegramScraperQueue stopped")

    async def _process_queue(self):
        """Worker that processes queued tasks"""
        while self.running:
            try:
                task_func, args, kwargs, future = await self.queue.get()
                try:
                    result = await task_func(self.client, *args, **kwargs)
                    future.set_result(result)
                except Exception as e:
                    logger.error(f"Error processing task: {str(e)}", exc_info=True)
                    future.set_exception(e)
                finally:
                    self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Unexpected error in queue processor: {str(e)}", exc_info=True)

    async def _enqueue_task(self, task_func, *args, **kwargs):
        """Add a task to the queue and wait for result"""
        if not self.running:
            await self.start()

        future = asyncio.Future()
        await self.queue.put((task_func, args, kwargs, future))
        return await future

    async def get_today_messages(self, channel_id: int):
        """Queue a task to get today's messages"""
        return await self._enqueue_task(self._get_today_messages, channel_id)

    async def get_channel_id(self, channel: str):
        """Queue a task to get a channel ID"""
        return await self._enqueue_task(self._get_channel_id, channel)

    @staticmethod
    async def _get_today_messages(client: TelegramClient, channel_id: int):
        """The actual implementation of getting today's messages"""
        logger.info(f"Getting today messages for channel {channel_id}")

        break_date = datetime.now(tz=None).date() - timedelta(days=1)
        messages = {
            'meta': {'channel_id': channel_id, 'date': datetime.now(tz=None)},
            'messages': [],
        }

        async for message in client.iter_messages(channel_id):
            if message.date.date() < break_date:
                break
            message_text = message.text
            if message_text is None or message_text == '':
                continue

            messages['messages'].append({'id': message.id, 'text': message_text})
        return messages

    @staticmethod
    async def _get_channel_id(client: TelegramClient, channel: str):
        """The actual implementation of getting a channel ID"""
        logger.info(f"Getting channel ID for channel {channel}")

        try:
            entity = await client.get_entity(channel)
            channel_id = entity.id
            username = entity.username

            # For supergroups/channels, we need to get the negative ID
            if hasattr(entity, 'megagroup') or hasattr(entity, 'broadcast'):
                # Convert to channel ID format with -100 prefix
                channel_id = int(f"-100{channel_id}")

            logger.info(f"Found channel ID: {channel_id}")
            return channel_id, username

        except Exception as e:
            logger.error(f"Error getting channel ID for {channel}: {str(e)}")
            raise


# Create FastAPI application
app = FastAPI(
    title="Telegram Scraper Service",
    description="Microservice for scraping Telegram channels",
    version="1.0.0",
)

# Create a singleton queue instance
telegram_queue = TelegramScraperQueue(API_ID, API_HASH, SESSION_NAME)


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
    # Run the server if executed directly
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
