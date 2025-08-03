import asyncio
import logging
from datetime import datetime

from .enums import ResponseStatus
from ..data_types import FeedContent, Post
from ..db.repository import DatabaseRepository
from ..services.summarizer import generate_summary
from ..utils.scraper_utils import get_today_messages_by_channel_name
from ..utils.utils import log_async_performance

logger = logging.getLogger("news_aggregator")


class TelegramFeed:
    __slots__ = ("channel_id", "channel_name", "last_updated", "content")
    _client = None
    _scraper_url: str | None = None

    def __init__(self, channel_id: int, channel_name: str):
        self.channel_id = channel_id
        self.channel_name = channel_name
        self.last_updated = None
        self.content: FeedContent = {"posts": {}}

        logger.info(f"TelegramFeed {channel_id=} initialized")

    @classmethod
    def initialize(cls, client, scraper_url: str):
        cls._client = client
        cls._scraper_url = scraper_url

    @log_async_performance()
    async def _get_todays_posts(self) -> None:
        if self._scraper_url is None:
            raise ValueError("Scraper URL is not set")
        try:
            messages = await get_today_messages_by_channel_name(
                self.channel_name, self._scraper_url
            )
            logger.info(f"{len(messages)} messages received")
            updated_at = datetime.now()
            for message in reversed(messages["messages"]):
                if message["id"] not in self.content["posts"]:
                    message_data: Post = {
                        "updated_at": updated_at,
                        "text": message["text"],
                        "channel_id": self.channel_id,
                        "url": self._create_post_url(message["id"]),
                        "summary": None,
                        "id": message["id"],
                    }

                    self.content["posts"][message["id"]] = message_data

            self.last_updated = messages["meta"]["date"]

        except Exception as e:
            logger.error(f"Error updating {self.channel_id}: {str(e)}")

    @log_async_performance()
    async def update(self):
        """Update the feed with new content from the Telegram channel"""
        logger.info(f"Updating feed {self.channel_id} from channel {self.channel_id}")
        await self._get_todays_posts()
        await self._summarize_content()
        await self._add_content_to_db()
        logger.info(f"Feed {self.channel_id} updated.")

    @log_async_performance()
    async def _summarize_content(self):
        logger.info(f"Summarizing feed {self.channel_id}")

        tasks = []

        for post_id in self.content["posts"].keys():
            if self.content["posts"][post_id]["summary"] is None:
                text = self.content["posts"][post_id]["text"]
                tasks.append(self._get_or_generate_summary(self.channel_id, post_id, text))

        results = await asyncio.gather(*tasks)

        for post_id, summary in results:
            self.content["posts"][post_id]["summary"] = summary

        logger.info(f"Summarizing feed {self.channel_id} completed.")

    def _create_post_url(self, message_id: int):
        return f"https://t.me/{self.channel_name}/{message_id}"

    @log_async_performance()
    async def _add_content_to_db(self):
        for post_id, post_data in self.content["posts"].items():
            logger.info(f"Adding post {post_id} to database")
            result = await DatabaseRepository.add_post_to_db(
                post_id=post_id,
                text=post_data["text"],
                channel_id=self.channel_id,
                summary=post_data["summary"],
            )

            match result.status:
                case ResponseStatus.OK:
                    logger.info(f"Post {post_id} added to database")
                case ResponseStatus.ALREADY_EXISTS:
                    logger.info(f"Post {post_id} already exists in database")
                case _:
                    logger.info(
                        f"Post {post_id} not added to database. Error: {result.status}, message: {result.message}")

    def clear_cache(self):
        """Clearly cached posts and reset the last updated timestamp"""
        self.content["posts"] = {}
        logger.info(f"Cache cleared for channel {self.channel_id}")

    @log_async_performance()
    async def _get_or_generate_summary(self, channel_id: int, post_id: int, input_text: str):
        logger.info(f"Processing summary for post {post_id} from channel {channel_id}")
        result = await DatabaseRepository.get_post_summary(channel_id, post_id)
        
        if result.is_success and result.data:
            logger.info(f"Found summary in database for post {post_id} from channel {channel_id}")
            summary = result.data["summary"]
            return post_id, summary
        elif result.is_error:
            logger.error(f"Error retrieving summary from database for post {post_id} from channel {channel_id}: {result.message}")

        logger.info(f"No summary found in database for post {post_id} from channel {channel_id}. Generating a new one")
        new_summary = await generate_summary(client=self._client, input_text=input_text)
        return post_id, new_summary.text
