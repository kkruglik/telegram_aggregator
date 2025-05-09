import asyncio
import logging
from datetime import time

from aiogram import Bot

from ..db.repository import DatabaseRepository
from ..utils.utils import get_timezone_string
from .feed import TelegramFeed
from .enums import ResponseStatus, UserResponse

logger = logging.getLogger("news_aggregator")


class User:
    _bot = None
    __slots__ = ("id", "_user_feeds", "notification_time", "timezone", "is_premium")

    def __init__(
        self,
        user_id: int,
        notification_time: time = None,
        timezone: str = None,
        is_premium: bool = False,
    ):
        self.id = user_id
        self._user_feeds: dict[int, TelegramFeed] = {}
        self.notification_time = notification_time
        self.timezone = timezone
        self.is_premium = is_premium

        logger.debug(f"User {user_id} initialized")

    @classmethod
    def set_bot(cls, bot: Bot):
        cls._bot = bot

    @property
    def is_user_registered(self):
        return all([self.notification_time, self.timezone])

    def set_timezone(self, lat: float, lon: float):
        logger.info(f"Setting location to {lat}, {lon}")
        self.timezone = get_timezone_string(lat, lon)
        logger.info(f"Setting timezone to {self.timezone}")

    def set_notification_time(self, notification_time: time):
        logger.info(f"Setting notification time to {notification_time}")
        self.notification_time = notification_time

    async def subscribe(self, feed: TelegramFeed) -> UserResponse:
        logger.info(f"User {self.id} subscribing to feed {feed.channel_id}")

        if feed.channel_id in self._user_feeds:
            logger.info(f"User {self.id} already subscribed to feed {feed.channel_id}, skipping")
            return UserResponse.error(ResponseStatus.ALREADY_SUBSCRIBED)

        if not self.is_premium and len(self._user_feeds) >= 5:
            logger.info(f"User {self.id} exceeded max number of feeds, skipping")
            return UserResponse.error(ResponseStatus.LIMIT_REACHED)

        try:
            self._user_feeds[feed.channel_id] = feed
            await DatabaseRepository.subscribe_to_feed(self.id, feed.channel_id)
            return UserResponse.success()
        except Exception as e:
            logger.error(f"Failed to subscribe user {self.id} to feed {feed.channel_id}: {e}")
            return UserResponse.error(ResponseStatus.DATABASE_ERROR)

    async def unsubscribe(self, channel_id: int):
        if channel_id in self._user_feeds:
            logger.info(f"User {self.id} unsubscribing from feed {channel_id}")
            del self._user_feeds[channel_id]
            await DatabaseRepository.unsubscribe_from_feed(self.id, channel_id)
            logger.info(f"User {self.id} now subscribed to {len(self._user_feeds)} feeds")
        else:
            logger.warning(
                f"User {self.id} tried to unsubscribe from non-existent feed {channel_id}"
            )

    def get_user_feeds(self):
        logger.debug(f"Retrieved feed list for user {self.id}")
        return self._user_feeds

    async def update_users_feeds(self):
        logger.info(f"Updating users feeds {self.id}: {len(self._user_feeds)} feeds")
        tasks = [feed.update() for feed in self._user_feeds.values()]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for feed, result in zip(self._user_feeds.values(), results):
            if isinstance(result, Exception):
                logger.error(
                    f"Failed to update feed {feed.channel_id} for user {self.id}: {str(result)}"
                )
                logger.error("Exception details:", exc_info=result)

        logger.info(f"Completed feed updates for user {self.id}")

    async def send_feed_update(self):
        logger.info(f"Send feed update for user {self.id}")
        MESSAGE_LIMIT = 4096
        for feed_name, feed in self._user_feeds.items():
            if not feed.content["posts"]:
                logger.info(f"Feed {feed_name} is empty, skipping")
                continue

            todays_feed = f"{feed.channel_name} feed: \n\n"
            feed_content = feed.content["posts"]
            post_ids = list(feed_content.keys())
            for post_id in post_ids:
                post_content = feed_content[post_id]
                todays_feed += f"{post_content['summary']} \n{post_content['url']}\n\n---\n\n"
                del feed_content[post_id]

            if len(todays_feed) > MESSAGE_LIMIT:
                for i in range(0, len(todays_feed), MESSAGE_LIMIT):
                    todays_feed_part = todays_feed[i : i + MESSAGE_LIMIT]
                    await self._bot.send_message(chat_id=self.id, text=todays_feed_part)
                    await asyncio.sleep(1)

            else:
                await self._bot.send_message(
                    chat_id=self.id,
                    text=todays_feed,
                )
                await asyncio.sleep(1)

        for feed in self._user_feeds.values():
            feed._clear_cache()

    async def save_user_to_database(self):
        """Save current user state to database"""
        logger.info(f"Saving user {self.id} to database")
        await DatabaseRepository.update_user(
            user_id=self.id,
            notification_time=self.notification_time,
            timezone=self.timezone,
        )

    async def upgrade_user_to_premium(self):
        """Upgrade user to premium status"""
        logger.info(f"Upgrading user {self.id} to premium")
        self.is_premium = True
        await DatabaseRepository.update_user(self.id, is_premium=True)
        logger.info(f"User {self.id} upgraded to premium")
