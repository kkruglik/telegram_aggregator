from telethon.types import Channel
import asyncio
import logging
from datetime import datetime, timedelta, timezone


from telethon.errors import FloodWaitError
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from telethon import TelegramClient

from ..config import config

logger = logging.getLogger("news_aggregator")


class TelegramScraperQueue:
    def __init__(self, api_id: int, api_hash: str, session_name: str):
        self.client = TelegramClient(session_name, api_id, api_hash)
        self.queue = asyncio.Queue()
        self.running = False
        self.worker_task = None

    @retry(
        retry=retry_if_exception_type((ConnectionError, OSError, TimeoutError, FloodWaitError)),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        stop=stop_after_attempt(3),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    async def start(self):
        """Start the queue worker"""
        if self.running and self.worker_task and not self.worker_task.done():
            logger.info("TelegramScraperQueue already running, skipping start")
            return

        if not self.client.is_connected():
            logger.info("Client is not running. Starting...")
            try:
                self.client.start()
            except Exception as e:
                logger.error(f"Error starting client: {e}")
                raise

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
        logger.debug(f"Queue worker started, current queue size={self.queue.qsize()}")
        while self.running:
            if not self.client.is_connected():
                logger.warning("TelegramScraperQueue client not connected. Reconnecting...")
                try:
                    await asyncio.wait_for(self.client.connect(), timeout=10)
                    logger.info("Reconnection successful")
                except asyncio.TimeoutError:
                    logger.error("Reconnection timed out after 10 seconds")
                    await asyncio.sleep(5)
                    continue
                except Exception as e:
                    logger.error(f"Reconnection failed: {str(e)}")
                    await asyncio.sleep(5)
                    continue

            logger.debug(f"Queue worker waiting for next task, queue size={self.queue.qsize()}")
            try:
                task_func, args, kwargs, future = await self.queue.get()
                logger.info(
                    f"Queue worker picked up: {task_func.__name__} kwargs={kwargs}, remaining={self.queue.qsize()}"
                )
                try:
                    result = await task_func(self.client, *args, **kwargs)
                    if not future.cancelled():
                        future.set_result(result)
                    logger.info(f"Queue worker done: {task_func.__name__} kwargs={kwargs}")
                except Exception as e:
                    logger.error(
                        f"Error processing task {task_func.__name__}: {str(e)}", exc_info=True
                    )
                    if not future.cancelled():
                        future.set_exception(e)
                finally:
                    self.queue.task_done()
            except asyncio.CancelledError:
                logger.info("Queue worker cancelled")
                break
            except Exception as e:
                logger.error(f"Unexpected error in queue processor: {str(e)}", exc_info=True)
        logger.info("Queue worker exited")

    async def _enqueue_task(self, task_func, *args, **kwargs):
        logger.info(
            f"Enqueuing {task_func.__name__} kwargs={kwargs}, queue size before={self.queue.qsize()}"
        )
        future = asyncio.Future()
        await self.queue.put((task_func, args, kwargs, future))
        logger.info(
            f"Enqueued {task_func.__name__} kwargs={kwargs}, queue size after={self.queue.qsize()}"
        )
        try:
            return await asyncio.wait_for(future, timeout=60)
        except asyncio.TimeoutError:
            future.cancel()
            logger.error(f"Task {task_func.__name__} kwargs={kwargs} timed out after 60s")
            raise

    async def get_today_messages_by_id(self, channel_id: int):
        """Queue a task to get today's messages"""
        return await self._enqueue_task(self._get_today_messages, channel_id=channel_id)

    async def get_today_messages_by_name(self, channel_name: str):
        """Queue a task to get today's messages"""
        return await self._enqueue_task(self._get_today_messages, channel_name=channel_name)

    async def get_channel_id(self, channel: str):
        """Queue a task to get a channel ID"""
        return await self._enqueue_task(self._get_channel_id, channel)

    @staticmethod
    @retry(
        retry=retry_if_exception_type((ConnectionError, OSError, TimeoutError, FloodWaitError)),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        stop=stop_after_attempt(3),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    async def _get_today_messages(
        client: TelegramClient, channel_id: int | None = None, channel_name: str | None = None
    ):
        """Get messages from the last 24 hours"""
        channel_entity = channel_name or channel_id

        if channel_entity is None:
            raise ValueError("Either channel_id or channel_name must be provided")

        logger.info(f"Getting messages from last 24 hours for channel {channel_entity}")

        # Make cutoff_time timezone-aware by using UTC
        cutoff_time = datetime.now(tz=timezone.utc) - timedelta(hours=24)

        messages = {
            "meta": {
                "channel_id": channel_entity,
                "date": datetime.now(tz=timezone.utc),
            },
            "messages": [],
        }

        try:
            async for message in client.iter_messages(
                entity=channel_entity,
                limit=100,
                offset_date=datetime.now(tz=timezone.utc),
            ):
                # Now both dates have timezone info and can be compared
                if message.date < cutoff_time:
                    break

                message_text = message.text
                if message_text is None or message_text == "":
                    continue

                messages["messages"].append({"id": message.id, "text": message_text})

            return messages
        except Exception as e:
            logger.error(f"Error fetching messages for channel {channel_id}: {str(e)}")
            raise

    @staticmethod
    @retry(
        retry=retry_if_exception_type((ConnectionError, OSError, TimeoutError, FloodWaitError)),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        stop=stop_after_attempt(3),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    async def _get_channel_id(client: TelegramClient, channel: str):
        """The actual implementation of getting a channel ID"""
        logger.info(f"Getting channel ID for channel {channel}")

        try:
            entity = await client.get_entity(channel)
            if not isinstance(entity, Channel):
                raise ValueError(f"Output entity of {channel} is not a channel. Output: {entity}")

            channel_id = entity.id
            username = entity.username

            # For supergroups/channels, we need to get the negative ID
            if hasattr(entity, "megagroup") or hasattr(entity, "broadcast"):
                # Convert to channel ID format with -100 prefix
                channel_id = int(f"-100{channel_id}")

            logger.info(f"Found channel ID: {channel_id}")
            return channel_id, username

        except Exception as e:
            logger.error(f"Error getting channel ID for {channel}: {str(e)}")
            raise


scraper_client = TelegramScraperQueue(
    config.scraper.api_id, config.scraper.api_hash, config.scraper.session_name
)
