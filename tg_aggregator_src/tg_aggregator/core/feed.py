import asyncio
import logging
from datetime import datetime

from ..services.summarizer import generate_summary
from ..data_types import FeedContent, Post
from ..utils.scraper_utils import get_today_messages_by_channel_name
from ..db.repository import DatabaseRepository

logger = logging.getLogger("news_aggregator")


class TelegramFeed:
    __slots__ = ("channel_id", "channel_name", "last_updated", "content")
    _client = None
    _scraper_url = None

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

    async def _get_todays_posts(self):
        try:
            messages = await get_today_messages_by_channel_name(
                self.channel_name, self._scraper_url
            )
            logger.info(f"{len(messages)} messages received")
            updated_at = datetime.now()
            for message in messages["messages"]:
                if message["id"] not in self.content["posts"]:
                    message_data: Post = {}
                    message_data["updated_at"] = updated_at
                    message_data["text"] = message["text"]
                    message_data["channel_id"] = self.channel_id
                    message_data["url"] = self._create_post_url(message["id"])
                    message_data["summary"] = None
                    message_data["id"] = message["id"]

                    self.content["posts"][message["id"]] = message_data

            self.last_updated = messages["meta"]["date"]

        except Exception as e:
            logger.error(f"Error updating {self.channel_id}: {str(e)}")

    async def update(self):
        """Update the feed with new content from the Telegram channel"""
        logger.info(f"Updating feed {self.channel_id} from channel {self.channel_id}")
        await self._get_todays_posts()
        await self._summarize_content()
        await self._add_content_to_db()
        logger.info(f"Feed {self.channel_id} updated.")

    async def _summarize_content(self):
        async def summarize_wrapper(post_id, text):
            summary = await generate_summary(client=self._client, input_text=text)
            return post_id, summary

        logger.info(f"Summarizing feed {self.channel_id}")

        tasks = []

        for post_id in self.content["posts"].keys():
            if self.content["posts"][post_id]["summary"] is None:
                text = self.content["posts"][post_id]["text"]
                tasks.append(summarize_wrapper(post_id, text))

        results = await asyncio.gather(*tasks)

        for post_id, response in results:
            self.content["posts"][post_id]["summary"] = response.text

        logger.info(f"Summarizing feed {self.channel_id} completed.")

    def _create_post_url(self, message_id: int):
        return f"https://t.me/{self.channel_name}/{message_id}"

    async def _add_content_to_db(self):
        for post_id, post_data in self.content["posts"].items():
            logger.info(f"Adding post {post_id} to database")
            await DatabaseRepository.add_post_to_db(
                post_id, post_data["text"], self.channel_id, post_data["summary"]
            )

    def _clear_cache(self):
        """Clear cached posts and reset last updated timestamp"""
        self.content["posts"] = {}
        logger.info(f"Cache cleared for channel {self.channel_id}")
