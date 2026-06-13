import asyncio
import logging
from datetime import time


from aiogram import Bot  # type: ignore

from ..db.repository import DatabaseRepository
from .feed import TelegramFeed
from .enums import ResponseStatus, Response
from ..utils.utils import log_async_performance
from ..utils.text import find_matched_keyword

logger = logging.getLogger("news_aggregator")


class User:
    _bot = None
    __slots__ = (
        "id",
        "user_feeds",
        "notification_time",
        "timezone",
        "is_premium",
        "channel_filters",
    )

    def __init__(
        self,
        user_id: int,
        notification_time: time | None = None,
        timezone: str | None = "EET",
        is_premium: bool = False,
        channel_filters: dict[int, set[str]] | None = None,
    ):
        self.id = user_id
        self.user_feeds: dict[int, TelegramFeed] = {}
        self.notification_time = notification_time
        self.timezone = timezone
        self.is_premium = is_premium

        if channel_filters is None:
            self.channel_filters = {}
        else:
            self.channel_filters = channel_filters

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
        result = await DatabaseRepository.update_user(self.id, timezone=self.timezone)
        if result.is_success:
            logger.info(f"Successfully updated timezone to {self.timezone}")
        else:
            logger.error(f"Failed to update timezone to {self.timezone}: {result.message}")

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
            result = await DatabaseRepository.unsubscribe_from_feed(self.id, channel_id)
            if result.is_success:
                logger.info(f"User {self.id} successfully unsubscribed from feed {channel_id}")
                return result
            else:
                logger.error(f"Failed to unsubscribe from feed {channel_id}: {result.message}")
                return result

    async def add_channel_filters(self, channel_id: int, keywords: set[str]):
        existing = self.channel_filters.get(channel_id, set())
        self.channel_filters[channel_id] = existing | keywords
        logger.info(
            f"User {self.id} appending keywords {keywords} to channel {channel_id}. Total: {self.channel_filters[channel_id]}"
        )
        await DatabaseRepository.update_user_channels_filters(self.id, self.channel_filters)
        logger.info(f"User {self.id} channel {channel_id} filters saved")

    async def clear_channel_filters(self, channel_id: int):
        self.channel_filters.pop(channel_id, None)
        logger.info(f"User {self.id} cleared filters for channel {channel_id}")
        await DatabaseRepository.update_user_channels_filters(self.id, self.channel_filters)
        logger.info(f"User {self.id} channel {channel_id} filters cleared in db")

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
        logger.info(
            f"Send feed update for user {self.id}: feeds={list(self.user_feeds.keys())}, "
            f"channel_filters={self.channel_filters}"
        )
        MESSAGE_LIMIT = 4096
        for feed_name, feed in self.user_feeds.items():
            if not feed.content["posts"]:
                logger.info(
                    f"User {self.id} feed {feed.channel_id} ({feed.channel_name}) is empty, skipping"
                )
                continue

            feed_filters = self.channel_filters.get(feed.channel_id, set())
            logger.info(
                f"User {self.id} feed {feed.channel_id} ({feed.channel_name}): {len(feed_filters)} filters active: {feed_filters}"
            )

            feed_header = f"<b>@{feed.channel_name} feed</b>: \n\n"
            feed_content = feed.content["posts"]
            post_ids = list(feed_content.keys())

            current_message = feed_header

            for post_id in post_ids:
                post_content = feed_content[post_id]

                if feed_filters:
                    matched = find_matched_keyword(post_content["text"], feed_filters)
                    if matched is None:
                        logger.info(
                            f"User {self.id} post {post_id} skipped: no keywords matched for channel {feed.channel_id}"
                        )
                        continue
                    keyword_label = f"🔍 <i>{matched}</i>\n"
                else:
                    keyword_label = ""

                post_text = (
                    f"{keyword_label}{post_content['summary']} \n{post_content['url']}\n\n---\n\n"
                )

                if len(current_message + post_text) > MESSAGE_LIMIT:
                    try:
                        await self._bot.send_message(
                            chat_id=self.id, text=current_message, parse_mode="HTML"
                        )
                    except Exception as e:
                        logger.error(f"Failed to send message to user {self.id}: {e}")
                    await asyncio.sleep(1)

                    current_message = feed_header + post_text
                else:
                    current_message += post_text

                del feed_content[post_id]

            if current_message != feed_header:
                try:
                    await self._bot.send_message(
                        chat_id=self.id, text=current_message, parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(f"Failed to send message to user {self.id}: {e}")
                await asyncio.sleep(1)

        for feed in self.user_feeds.values():
            feed.clear_cache()

    @log_async_performance()
    async def save_user_to_database(self):
        """Save the current user state to a database"""
        logger.info(f"Saving user {self.id} to database")
        result = await DatabaseRepository.update_user(
            user_id=self.id,
            notification_time=self.notification_time,
            timezone=self.timezone,
        )
        if result.is_success:
            logger.info(f"User {self.id} saved to database")
        else:
            logger.error(f"Failed to save user {self.id} to database: {result.message}")

    @log_async_performance()
    async def upgrade_user_to_premium(self):
        """Upgrade user to premium status"""
        logger.info(f"Upgrading user {self.id} to premium")
        self.is_premium = True
        result = await DatabaseRepository.update_user(self.id, is_premium=True)
        if result.is_success:
            logger.info(f"User successfully {self.id} upgraded to premium")
        else:
            logger.error(f"Failed to upgrade user {self.id} to premium: {result.message}")
