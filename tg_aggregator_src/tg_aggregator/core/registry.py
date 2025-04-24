import asyncio
import logging
from datetime import timedelta, datetime

from ..db.repository import DatabaseRepository
from ..services.tasks_scheduler import TasksScheduler
from ..utils.scraper_utils import get_channel_id
from .feed import TelegramFeed
from .user import User

logger = logging.getLogger('news_aggregator')


class UserRegistry:
    _users: dict[int, User] = {}
    _scheduler = TasksScheduler()

    @classmethod
    async def initialize(cls, ) -> None:
        cls._scheduler.start()
        await cls._load_users_from_db()

    @classmethod
    async def _load_users_from_db(cls) -> None:
        existing_users = await DatabaseRepository.get_all_users()
        for user in existing_users:
            user_id, user_tz, notification_time = user['id'], user['timezone'], user['notification_time']
            user_cls = User(user_id, notification_time, user_tz)
            cls._users[user_id] = user_cls
            logger.info(f"User {user_id}|{user_tz}|{notification_time} loaded from db.")
            cls.schedule_user_updates(user_id)

        users_feeds = await DatabaseRepository.get_user_feed_associations()

        for row in users_feeds:
            user_id, feed_id = row['user_id'], row['feed_id']
            user = cls._users.get(user_id, None)
            feed = FeedsRegistry._feeds.get(feed_id, None)
            if user and feed:
                user._user_feeds[feed_id] = feed
                logger.info(f"Added feed {feed.channel_name} to user {user.id}.")
            else:
                logger.warning(f"User {user_id}|{feed_id} not found.")

    @classmethod
    async def get_or_create_user(cls, user_id: int) -> User:
        if user_id in cls._users:
            logger.info(f"[UserRegistry] User {user_id} already registered.")
            return cls._users[user_id]

        user_record = await DatabaseRepository.get_user(user_id)

        if user_record:
            user = User(user_id)
            cls._users[user_id] = user
            logger.info(f"[UserRegistry] User {user_id} registered successfully")
            return user
        else:
            logger.info(f"[UserRegistry] Creating new user {user_id}.")
            await DatabaseRepository.create_user(user_id, None)
            user = User(user_id)

        cls._users[user_id] = user
        logger.info(f"[UserRegistry] User {user_id} loaded/created successfully")
        return user

    @classmethod
    def delete_user(cls, user_id) -> None:
        logger.info(f"[UserRegistry] Deleting user {user_id}")
        user = cls._users[user_id]

        feed_names = list(user._user_feeds.keys())
        if feed_names:
            logger.info(f"[UserRegistry] Unsubscribing user {user_id} from feeds: {feed_names}")
            for feed_name in feed_names:
                user.unsubscribe(feed_name)

        del cls._users[user_id]
        logger.info(f"[UserRegistry] User {user_id} deleted")

    @classmethod
    def schedule_user_updates(cls, user_id: int) -> None:
        logger.info(f"[UserRegistry] Scheduling user updates for user {user_id}")
        user = cls._users[user_id]

        notification_time = user.notification_time
        user_timezone = user.timezone
        update_minute = (notification_time.minute - 5) % 60
        update_hour = notification_time.hour if notification_time.minute > 0 else (notification_time.hour - 1) % 24

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

        logger.info(f"[UserRegistry] Scheduled notifications for user {user} at {notification_time.hour}:{notification_time.minute}:{user_timezone}")
        logger.info(f"[UserRegistry] Scheduled feed update for user {user} at {update_hour}:{update_minute}:{user_timezone}")



class FeedsRegistry:
    _feeds: dict[int, TelegramFeed] = {}
    _feeds_users_count: dict[int, int] = {}

    @classmethod
    async def initialize(cls) -> None:
        await cls._load_feeds_from_db()

    @classmethod
    async def _load_feeds_from_db(cls) -> None:
        logger.info(f"[FeedsRegistry] Loading feeds from db.")
        existing_feeds = await DatabaseRepository.get_all_feeds()
        for feed in existing_feeds:
            channel_id, channel_name = feed['id'], feed['channel_name']
            cls._feeds[channel_id] = TelegramFeed(channel_id, channel_name)
            cls._feeds_users_count[channel_id] = 1
            logger.info(f"Feed {channel_id}|{channel_name} loaded from db.")

        logger.info(f"[FeedsRegistry] Finished loading feeds from db.")

    @classmethod
    async def update_all_feeds(cls) -> None:
        logger.info(f"[FeedsRegistry] Updating all {len(cls._feeds)} feeds")
        tasks = [feed.update() for feed in cls._feeds.values()]
        await asyncio.gather(*tasks)

    @classmethod
    def get_feed_by_id(cls, feed_id: int) -> TelegramFeed:
        logger.info(f"[FeedsRegistry] Getting feed by id {feed_id}")
        return cls._feeds[feed_id]

    @classmethod
    async def create_or_get_feed(cls, feed_name: str):
        channel_id, channel_name = await get_channel_id(feed_name)
        if channel_id is None:
            raise ValueError(f"[FeedsRegistry] Feed {feed_name} not found.")

        if channel_id in cls._feeds:
            cls._feeds_users_count[channel_id] += 1
            logger.info(
                f"[FeedsRegistry] Feed {feed_name} already exists, subscriber count increased to {cls._feeds_users_count[channel_id]}")
        else:
            await DatabaseRepository.create_feed(channel_id, channel_name)
            cls._feeds[channel_id] = TelegramFeed(channel_id, channel_name)
            cls._feeds_users_count[channel_id] = 1
            logger.info(f"[FeedsRegistry] New feed {channel_id} created with 1 subscriber")

        return cls._feeds[channel_id]

    @classmethod
    def release_feed(cls, channel_id: int):
        # TODO fix channels_id/name confuse
        if channel_id in cls._feeds:
            cls._feeds_users_count[channel_id] -= 1
            current_count = cls._feeds_users_count[channel_id]
            logger.info(f"[FeedsRegistry] Feed {channel_id} subscriber count decreased to {current_count}")

            # TODO _feeds_users_count logic is totaly broken
            # if current_count <= 0:
            #     del cls._feeds[channel_id]
            #     del cls._feeds_users_count[channel_id]
            #     logger.info(f"[FeedsRegistry] Feed {channel_id} removed - no subscribers left")
        else:
            logger.warning(f"[FeedsRegistry] Cannot release feed {channel_id} - not found")
