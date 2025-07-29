import asyncio
import logging
from datetime import time

from aiogram import Bot  # type: ignore

from ..db.repository import DatabaseRepository
from .feed import TelegramFeed
from .enums import ResponseStatus, Response
from ..utils.utils import log_async_performance

logger = logging.getLogger("news_aggregator")


class User:
    _bot = None
    __slots__ = ("id", "user_feeds", "notification_time", "timezone", "is_premium")

    def __init__(
            self,
            user_id: int,
            notification_time: time | None = None,
            timezone: str | None = "EET",
            is_premium: bool = False,
    ):
        self.id = user_id
        self.user_feeds: dict[int, TelegramFeed] = {}
        self.notification_time = notification_time
        self.timezone = timezone
        self.is_premium = is_premium

        logger.debug(f"User {user_id} initialized")

    @classmethod
    def initialize(cls, bot: Bot):
        cls._bot = bot

    @property
    def is_user_registered(self):
        return all([self.notification_time, self.timezone])

    @log_async_performance()
    async def set_timezone(self, timezone: str):
        logger.info(f"Setting user timezone: {timezone}")
        self.timezone = timezone
        await DatabaseRepository.update_user(self.id, timezone=self.timezone)
        logger.info(f"Setting timezone to {self.timezone}")

    def set_notification_time(self, notification_time: time):
        logger.info(f"Setting notification time to {notification_time}")
        self.notification_time = notification_time

    @log_async_performance()
    async def subscribe(self, feed: TelegramFeed) -> Response:
        logger.info(f"User {self.id} subscribing to feed {feed.channel_id}")

        if feed.channel_id in self.user_feeds:
            logger.info(f"User {self.id} already subscribed to feed {feed.channel_id}, skipping")
            return Response.error(ResponseStatus.ALREADY_SUBSCRIBED)

        if not self.is_premium and len(self.user_feeds) >= 5:
            logger.info(f"User {self.id} exceeded max number of feeds, skipping")
            return Response.error(ResponseStatus.LIMIT_REACHED)

        self.user_feeds[feed.channel_id] = feed
        return await DatabaseRepository.subscribe_to_feed(self.id, feed.channel_id)

    @log_async_performance()
    async def unsubscribe(self, channel_id: int):
        if channel_id in self.user_feeds:
            logger.info(f"User {self.id} unsubscribing from feed {channel_id}")
            del self.user_feeds[channel_id]
            return await DatabaseRepository.unsubscribe_from_feed(self.id, channel_id)

    def get_user_feeds(self):
        logger.debug(f"Retrieved feed list for user {self.id}")
        return self.user_feeds

    @log_async_performance()
    async def update_users_feeds(self):
        logger.info(f"Updating users feeds {self.id}: {len(self.user_feeds)} feeds")
        tasks = [feed.update() for feed in self.user_feeds.values()]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for feed, result in zip(self.user_feeds.values(), results):
            if isinstance(result, Exception):
                logger.error(
                    f"Failed to update feed {feed.channel_id} for user {self.id}: {str(result)}"
                )
                logger.error("Exception details:", exc_info=result)

        logger.info(f"Completed feed updates for user {self.id}")

    @log_async_performance()
    async def send_feed_update(self):
        logger.info(f"Send feed update for user {self.id}")
        MESSAGE_LIMIT = 4096
        for feed_name, feed in self.user_feeds.items():
            if not feed.content["posts"]:
                logger.info(f"Feed {feed_name} is empty, skipping")
                continue

            feed_header = f"<b>@{feed.channel_name} feed</b>: \n\n"
            feed_content = feed.content["posts"]
            post_ids = list(feed_content.keys())

            current_message = feed_header

            for post_id in post_ids:
                post_content = feed_content[post_id]
                post_text = f"{post_content['summary']} \n{post_content['url']}\n\n---\n\n"

                if len(current_message + post_text) > MESSAGE_LIMIT:
                    await self._bot.send_message(
                        chat_id=self.id,
                        text=current_message,
                        parse_mode="HTML"
                    )
                    await asyncio.sleep(1)

                    current_message = feed_header + post_text
                else:
                    current_message += post_text

                del feed_content[post_id]

            if current_message != feed_header:
                await self._bot.send_message(
                    chat_id=self.id,
                    text=current_message,
                    parse_mode="HTML"
                )
                await asyncio.sleep(1)

        for feed in self.user_feeds.values():
            feed.clear_cache()

    @log_async_performance()
    async def save_user_to_database(self):
        """Save the current user state to a database"""
        logger.info(f"Saving user {self.id} to database")
        await DatabaseRepository.update_user(
            user_id=self.id,
            notification_time=self.notification_time,
            timezone=self.timezone,
        )

    @log_async_performance()
    async def upgrade_user_to_premium(self):
        """Upgrade user to premium status"""
        logger.info(f"Upgrading user {self.id} to premium")
        self.is_premium = True
        await DatabaseRepository.update_user(self.id, is_premium=True)
        logger.info(f"User {self.id} upgraded to premium")
