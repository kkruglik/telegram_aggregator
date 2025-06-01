import asyncio
import logging

from ..db.repository import DatabaseRepository
from ..services.tasks_scheduler import TasksScheduler
from ..utils.scraper_utils import get_channel_id
from .feed import TelegramFeed
from .user import User

logger = logging.getLogger("news_aggregator")


class UserRegistry:
    _users: dict[int, User] = {}
    _scheduler = TasksScheduler()

    @classmethod
    async def initialize(cls) -> None:
        cls._scheduler.start()
        await cls._load_users_from_db()

    @classmethod
    async def _load_users_from_db(cls) -> None:
        existing_users = await DatabaseRepository.get_all_users()
        for user in existing_users:
            user_id, user_tz, notification_time, is_premium = (
                user["id"],
                user["timezone"],
                user["notification_time"],
                user["is_premium"],
            )
            user_cls = User(user_id, notification_time, user_tz, is_premium)
            cls._users[user_id] = user_cls
            logger.info(f"User {user_id}|{user_tz}|{notification_time} loaded from db.")
            cls.schedule_user_updates(user_id)

        users_feeds = await DatabaseRepository.get_user_feed_associations()

        for row in users_feeds:
            user_id, feed_id = row["user_id"], row["feed_id"]
            user = cls._users.get(user_id, None)
            feed = FeedsRegistry.feeds.get(feed_id, None)
            if user and feed:
                user.user_feeds[feed_id] = feed
                logger.info(f"Added feed {feed.channel_name} to user {user.id}.")
            else:
                logger.warning(f"User {user_id}|{feed_id} not found.")

    @classmethod
    async def get_or_create_user(cls, user_id: int) -> User:
        if user_id in cls._users:
            logger.info(f"User {user_id} already registered.")
            return cls._users[user_id]

        user_record = await DatabaseRepository.get_user(user_id)

        if user_record:
            user = User(user_id)
            cls._users[user_id] = user
            logger.info(f"User {user_id} registered successfully")
            return user
        else:
            logger.info(f"Creating new user {user_id}.")
            await DatabaseRepository.create_user(user_id, None, False)
            user = User(user_id)

        cls._users[user_id] = user
        logger.info(f"User {user_id} loaded/created successfully")
        return user

    @classmethod
    async def delete_user(cls, user_id) -> None:
        logger.info(f"Deleting user {user_id}")
        user = cls._users[user_id]

        feed_names = list(user.user_feeds.keys())
        if feed_names:
            logger.info(f"Unsubscribing user {user_id} from feeds: {feed_names}")
            for feed_name in feed_names:
                await user.unsubscribe(feed_name)

        del cls._users[user_id]
        logger.info(f"User {user_id} deleted")

    @classmethod
    def schedule_user_updates(cls, user_id: int) -> None:
        logger.info(f"Scheduling user updates for user {user_id}")
        user = cls._users[user_id]

        notification_time = user.notification_time

        if notification_time is None:
            logger.error(f"User {user_id} has no notification time set.")
            raise ValueError(f"User {user_id} has no notification time set.")

        user_timezone = user.timezone

        if user_timezone is None:
            logger.error(f"User {user_id} has no timezone set.")
            raise ValueError(f"User {user_id} has no timezone set.")

        update_minute = (notification_time.minute - 5) % 60
        update_hour = (
            notification_time.hour
            if notification_time.minute > 0
            else (notification_time.hour - 1) % 24
        )

        cls._scheduler.add_job(
            func=user.update_users_feeds,
            job_id=f"{user.id}_update_users_feeds",
            cron=f"{update_minute} {update_hour} * * *",
            timezone_name=user_timezone,
        )

        cls._scheduler.add_job(
            func=user.send_feed_update,
            job_id=f"{user.id}_send_feed_update",
            cron=f"{notification_time.minute} {notification_time.hour} * * *",
            timezone_name=user_timezone,
        )

        logger.info(
            f"Scheduled notifications for user {user} at {notification_time.hour}:{notification_time.minute}:{user_timezone}"
        )
        logger.info(
            f"Scheduled feed update for user {user} at {update_hour}:{update_minute}:{user_timezone}"
        )


class FeedsRegistry:
    feeds: dict[int, TelegramFeed] = {}
    feeds_users_count: dict[int, int] = {}
    scraper_url = None

    @classmethod
    async def initialize(cls, scraper_url: str) -> None:
        await cls._load_feeds_from_db()
        cls.scraper_url = scraper_url

    @classmethod
    async def _load_feeds_from_db(cls) -> None:
        logger.info("Loading feeds from db.")
        existing_feeds = await DatabaseRepository.get_all_feeds()
        for feed in existing_feeds:
            channel_id, channel_name = feed["id"], feed["channel_name"]
            cls.feeds[channel_id] = TelegramFeed(channel_id, channel_name)
            cls.feeds_users_count[channel_id] = 1
            logger.info(f"Feed {channel_id}|{channel_name} loaded from db.")

        logger.info("Finished loading feeds from db.")

    @classmethod
    async def update_all_feeds(cls) -> None:
        logger.info(f"Updating all {len(cls.feeds)} feeds")
        tasks = [feed.update() for feed in cls.feeds.values()]
        await asyncio.gather(*tasks)

    @classmethod
    def get_feed_by_id(cls, feed_id: int) -> TelegramFeed:
        logger.info(f"Getting feed by id {feed_id}")
        return cls.feeds[feed_id]

    @classmethod
    async def create_or_get_feed(cls, feed_name: str):
        # TODO move this check to feed itself
        if cls.scraper_url is None:
            logger.error("Scraper URL is not set.")
            raise ValueError("Scraper URL is not set.")

        channel_id, channel_name = await get_channel_id(feed_name, cls.scraper_url)

        logger.info(f"Creating feed {feed_name} with id {channel_id} and name {channel_name}")
        if channel_id is None:
            raise ValueError(f"Feed {feed_name} not found.")

        if channel_id in cls.feeds:
            cls.feeds_users_count[channel_id] += 1
            logger.info(
                f"Feed {feed_name} already exists, subscriber count increased to {cls.feeds_users_count[channel_id]}"
            )
        else:
            await DatabaseRepository.create_feed(channel_id, channel_name)
            cls.feeds[channel_id] = TelegramFeed(channel_id, channel_name)
            cls.feeds_users_count[channel_id] = 1
            logger.info(f"New feed {channel_id} created with 1 subscriber")

        return cls.feeds[channel_id]

    @classmethod
    def release_feed(cls, channel_id: int):
        # TODO fix channels_id/name confuse
        if channel_id in cls.feeds:
            cls.feeds_users_count[channel_id] -= 1
            current_count = cls.feeds_users_count[channel_id]
            logger.info(f"Feed {channel_id} subscriber count decreased to {current_count}")

            # TODO _feeds_users_count logic is totaly broken
            # if current_count <= 0:
            #     del cls._feeds[channel_id]
            #     del cls._feeds_users_count[channel_id]
            #     logger.info(f"Feed {channel_id} removed - no subscribers left")
        else:
            logger.warning(f"Cannot release feed {channel_id} - not found")
