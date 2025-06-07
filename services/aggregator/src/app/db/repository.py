import logging
from contextlib import asynccontextmanager
from datetime import time

import asyncpg  # type: ignore

from .migrations_manager import MigrationManager

logger = logging.getLogger("news_aggregator")


class DatabaseRepository:
    _connection_pool = None
    _migration_manager = MigrationManager()

    @classmethod
    async def initialize(cls, dsn):
        """Initialize the connection pool"""
        logger.info("Initializing database connection pool")
        cls._connection_pool = await asyncpg.create_pool(dsn)
        await cls._migration_manager.run_migrations(cls._connection_pool)

    @classmethod
    @asynccontextmanager
    async def get_connection(cls):
        """Get a connection from the pool"""
        if cls._connection_pool is None:
            raise Exception("Database connection pool not initialized")

        async with cls._connection_pool.acquire() as connection:
            yield connection

    @classmethod
    def create_migration(cls, name):
        """Create a new migration file"""
        return cls._migration_manager.create_migration(name)

    @classmethod
    async def create_tables(cls):
        """Create the database tables"""
        async with cls.get_connection() as conn:
            await conn.execute("""
                               CREATE TABLE IF NOT EXISTS users
                               (
                                   id
                                              BIGINT
                                       PRIMARY
                                           KEY
                                       UNIQUE,
                                   notification_time
                                              TIME,
                                   timezone
                                              VARCHAR(100) DEFAULT 'EET',
                                   is_premium BOOLEAN      DEFAULT FALSE
                               )
                               """)

            await conn.execute("""
                               CREATE TABLE IF NOT EXISTS feeds
                               (
                                   id
                                       BIGINT
                                       PRIMARY
                                           KEY
                                       UNIQUE,
                                   channel_name
                                       VARCHAR(100)
                               )
                               """)

            await conn.execute("""
                               CREATE TABLE IF NOT EXISTS content
                               (
                                   post_id
                                       BIGINT
                                       PRIMARY
                                           KEY,
                                   text
                                       TEXT,
                                   summary
                                       TEXT,
                                   channel_id
                                       BIGINT
                                       REFERENCES
                                           feeds
                                               (
                                                id
                                                   ) ON DELETE CASCADE
                               )
                               """)

            await conn.execute("""
                               CREATE TABLE IF NOT EXISTS users_feeds
                               (
                                   user_id
                                           BIGINT
                                       REFERENCES
                                           users
                                               (
                                                id
                                                   ) ON DELETE CASCADE,
                                   feed_id BIGINT REFERENCES feeds
                                       (
                                        id
                                           )
                                       ON DELETE CASCADE,
                                   CONSTRAINT user_feed_pk PRIMARY KEY
                                       (
                                        user_id,
                                        feed_id
                                           )
                               )
                               """)

            await conn.execute("""
                               ALTER TABLE users
                                   ADD COLUMN IF NOT EXISTS is_premium BOOLEAN DEFAULT FALSE;
                               """)

    @classmethod
    async def create_user(
        cls, user_id: int, notification_time: time| None = None, is_premium: bool = False
    ):
        """Create a new user"""
        async with cls.get_connection() as conn:
            return await conn.fetchrow(
                """
                                       INSERT INTO users(id, notification_time, is_premium)
                                       VALUES ($1, $2)
                                       RETURNING *
                                       """,
                user_id,
                notification_time,
                is_premium,
            )

    @classmethod
    async def get_user(cls, user_id):
        """Get user by telegram ID"""
        async with cls.get_connection() as conn:
            return await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)

    @classmethod
    async def get_all_users(cls):
        """Get all users"""
        async with cls.get_connection() as conn:
            return await conn.fetch(
                """SELECT *
                   FROM users"""
            )

    @classmethod
    async def get_all_feeds(cls):
        """Get all feeds"""
        async with cls.get_connection() as conn:
            return await conn.fetch(
                """SELECT *
                   FROM feeds"""
            )

    @classmethod
    async def get_user_feed_associations(cls):
        """Get all users feeds"""
        async with cls.get_connection() as conn:
            return await conn.fetch(
                """SELECT *
                   FROM users_feeds"""
            )

    @classmethod
    async def update_user(cls, user_id, notification_time=None, timezone=None, is_premium=None):
        """
        Update user with specified fields
        """
        set_parts = []
        params = [user_id]  # First parameter is always the user_id
        param_index = 2

        if notification_time is not None:
            set_parts.append(f"notification_time = ${param_index}")
            params.append(notification_time)
            param_index += 1

        if timezone is not None:
            set_parts.append(f"timezone= ${param_index}")
            params.append(timezone)
            param_index += 1

        if is_premium is not None:
            set_parts.append(f"is_premium= ${param_index}")
            params.append(is_premium)
            param_index += 1

        if not set_parts:
            async with cls.get_connection() as conn:
                return await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)

        query = f"""
            UPDATE users
            SET {", ".join(set_parts)}
            WHERE id = $1
            RETURNING *
        """

        async with cls.get_connection() as conn:
            return await conn.fetchrow(query, *params)

    @classmethod
    async def create_feed(cls, channel_id: int, channel_name: str):
        """Create a new feed"""
        async with cls.get_connection() as conn:
            return await conn.fetchrow(
                """
                                       INSERT INTO feeds(id, channel_name)
                                       VALUES ($1, $2);
                                       """,
                channel_id,
                channel_name,
            )

    @classmethod
    async def get_feed(cls, channel_id: int):
        """Get feed by channel name"""
        async with cls.get_connection() as conn:
            return await conn.fetchrow("SELECT * FROM feeds WHERE id = $1", channel_id)

    @classmethod
    async def subscribe_to_feed(cls, user_id: int, channel_id: int):
        """Subscribe to a new feed"""
        async with cls.get_connection() as conn:
            try:
                user = await cls.get_user(user_id)
                feed = await cls.get_feed(channel_id)
                if user is None or feed is None:
                    raise ValueError("User ID or feed ID not found")

                existing = await conn.fetchrow(
                    """
                                               SELECT *
                                               FROM users_feeds
                                               WHERE user_id = $1
                                                 AND feed_id = $2
                                               """,
                    user_id,
                    channel_id,
                )

                if existing:
                    logger.info(f"User {user_id} already subscribed to feed {channel_id}")
                    return existing

                return await conn.fetchrow(
                    """
                                           INSERT INTO users_feeds(user_id, feed_id)
                                           VALUES ($1, $2)
                                           RETURNING *
                                           """,
                    user_id,
                    channel_id,
                )

            except asyncpg.UniqueViolationError:
                logger.info(f"Race condition: User {user_id} was subscribed to feed {channel_id}")
                return await conn.fetchrow(
                    """
                                           SELECT *
                                           FROM users_feeds
                                           WHERE user_id = $1
                                             AND feed_id = $2
                                           """,
                    user_id,
                    channel_id,
                )

            except Exception as e:
                logger.error(f"Error subscribing user {user_id} to feed {channel_id}: {e}")
                raise

    @classmethod
    async def unsubscribe_from_feed(cls, user_id: int, channel_id: int):
        """Unsubscribe from a feed"""
        try:
            async with cls.get_connection() as conn:
                existing_subscription = await conn.fetchrow(
                    """
                                                            SELECT user_id
                                                            FROM users_feeds
                                                            WHERE user_id = $1
                                                              AND feed_id = $2;
                                                            """,
                    user_id,
                    channel_id,
                )

                if not existing_subscription:
                    logger.info(f"No subscription found for user {user_id} and feed {channel_id}")
                    return None

                return await conn.execute(
                    """
                                          DELETE
                                          FROM users_feeds
                                          WHERE user_id = $1
                                            AND feed_id = $2;
                                          """,
                    user_id,
                    channel_id,
                )

        except Exception as e:
            logger.error(f"Error unsubscribing user {user_id} from feed {channel_id}: {e}")
            raise

    @classmethod
    async def add_post_to_db(cls, post_id: int, text: str, channel_id: int, summary: str = None):
        """Add a new post to the content table"""
        try:
            async with cls.get_connection() as conn:
                result = await conn.fetchrow(
                    """
                                             INSERT INTO content(post_id, text, summary, channel_id)
                                             VALUES ($1, $2, $3, $4)
                                             RETURNING *
                                             """,
                    post_id,
                    text,
                    summary,
                    channel_id,
                )
                logger.info(f"Successfully added post {post_id} from channel {channel_id}")
                return result
        except Exception as e:
            logger.error(f"Error adding post {post_id} from channel {channel_id}: {e}")
            raise

    @classmethod
    async def update_post_summary(cls, post_id: int, summary: str):
        """Update summary for existing post in the content table"""
        try:
            async with cls.get_connection() as conn:
                result = await conn.fetchrow(
                    """
                                             UPDATE content
                                             SET summary = $2
                                             WHERE post_id = $1
                                             RETURNING *
                                             """,
                    post_id,
                    summary,
                )
                if result:
                    logger.info(f"Successfully updated summary for post {post_id}")
                else:
                    logger.warning(f"No post found with ID {post_id}")
                return result
        except Exception as e:
            logger.error(f"Error updating summary for post {post_id}: {e}")
            raise

    @classmethod
    async def has_summary(cls, post_id: int) -> bool:
        """Check if post exists and has a non-empty summary"""
        try:
            async with cls.get_connection() as conn:
                result = await conn.fetchrow(
                    """
                                             SELECT summary
                                             FROM content
                                             WHERE post_id = $1
                                             """,
                    post_id,
                )
                return bool(result and result["summary"])
        except Exception as e:
            logger.error(f"Error checking summary for post {post_id}: {e}")
            raise
