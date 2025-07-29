import logging
from contextlib import asynccontextmanager
from datetime import time

import asyncpg  # type: ignore

from .migrations_manager import MigrationManager
from ..core.enums import Response, ResponseStatus

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
    async def _execute_fetchrow(cls, query: str, *args) -> Response:
        try:
            async with cls.get_connection() as conn:
                result = await conn.fetchrow(query, *args)
                return Response.success(data=result)

        except asyncpg.UniqueViolationError as e:
            msg = f"Unique constraint violation: {e}"
            logger.error(msg)
            return Response.error(status=ResponseStatus.UNIQUE_CONSTRAINT_VIOLATION, message=msg)

        except asyncpg.ForeignKeyViolationError as e:
            msg = f"Foreign key constraint violation: {e}"
            logger.error(msg)
            return Response.error(status=ResponseStatus.CONSTRAINT_VIOLATION, message=msg)

        except asyncpg.PostgresError as e:
            msg = f"Postgres error: {e}"
            logger.error(msg)
            return Response.error(status=ResponseStatus.DATABASE_ERROR, message=msg)

        except Exception as e:
            msg = f"Unknown database error: {e}"
            logger.error(msg)
            return Response.error(status=ResponseStatus.UNKNOWN_ERROR, message=msg)

    @classmethod
    async def _execute_execute(cls, query: str, *args) -> Response:
        try:
            async with cls.get_connection() as conn:
                result = await conn.execute(query, *args)
                return Response.success(data=result)

        except asyncpg.UniqueViolationError as e:
            msg = f"Unique constraint violation: {e}"
            logger.error(msg)
            return Response.error(status=ResponseStatus.UNIQUE_CONSTRAINT_VIOLATION, message=msg)

        except asyncpg.ForeignKeyViolationError as e:
            msg = f"Foreign key constraint violation: {e}"
            logger.error(msg)
            return Response.error(status=ResponseStatus.CONSTRAINT_VIOLATION, message=msg)

        except asyncpg.PostgresError as e:
            msg = f"Postgres error: {e}"
            logger.error(msg)
            return Response.error(status=ResponseStatus.DATABASE_ERROR, message=msg)

        except Exception as e:
            msg = f"Unknown database error: {e}"
            logger.error(msg)
            return Response.error(status=ResponseStatus.UNKNOWN_ERROR, message=msg)

    @classmethod
    async def _execute_fetch(cls, query: str, *args) -> Response:
        try:
            async with cls.get_connection() as conn:
                result = await conn.fetch(query, *args)
                return Response.success(data=result)

        except asyncpg.UniqueViolationError as e:
            msg = f"Unique constraint violation: {e}"
            logger.error(msg)
            return Response.error(status=ResponseStatus.UNIQUE_CONSTRAINT_VIOLATION, message=msg)

        except asyncpg.ForeignKeyViolationError as e:
            msg = f"Foreign key constraint violation: {e}"
            logger.error(msg)
            return Response.error(status=ResponseStatus.CONSTRAINT_VIOLATION, message=msg)

        except asyncpg.PostgresError as e:
            msg = f"Postgres error: {e}"
            logger.error(msg)
            return Response.error(status=ResponseStatus.DATABASE_ERROR, message=msg)

        except Exception as e:
            msg = f"Unknown database error: {e}"
            logger.error(msg)
            return Response.error(status=ResponseStatus.UNKNOWN_ERROR, message=msg)

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
            cls, user_id: int, notification_time: time | None = None, is_premium: bool = False
    ) -> Response:
        """Create a new user"""
        query = """
                INSERT INTO users(id, notification_time, is_premium)
                VALUES ($1, $2, $3)
                RETURNING *
                """
        result = await cls._execute_fetchrow(query, user_id, notification_time, is_premium)
        return result

    @classmethod
    async def get_user(cls, user_id):
        """Get user by telegram ID"""
        query = "SELECT * FROM users WHERE id = $1"
        result = await cls._execute_fetchrow(query, user_id)
        return result

    @classmethod
    async def get_all_users(cls):
        """Get all users"""
        return await cls._execute_fetch(
            """SELECT *
               FROM users"""
        )

    @classmethod
    async def get_all_feeds(cls):
        """Get all feeds"""
        return await cls._execute_fetch(
            """SELECT *
               FROM feeds"""
        )

    @classmethod
    async def get_user_feed_associations(cls):
        """Get all users feeds"""
        return await cls._execute_fetch(
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
            return await cls._execute_fetchrow(
                "SELECT * FROM users WHERE id = $1",
                user_id
            )

        query = f"""
            UPDATE users
            SET {", ".join(set_parts)}
            WHERE id = $1
            RETURNING *
        """
        result = await cls._execute_fetchrow(query, *params)
        return result

    @classmethod
    async def create_feed(cls, channel_id: int, channel_name: str):
        """Create a new feed"""
        query = """
                INSERT INTO feeds(id, channel_name)
                VALUES ($1, $2)
                ON CONFLICT (id) DO NOTHING;
                """
        result = await cls._execute_fetchrow(query, channel_id, channel_name)
        return result

    @classmethod
    async def get_feed(cls, channel_id: int):
        """Get feed by channel name"""
        query = "SELECT * FROM feeds WHERE id = $1"
        result = await cls._execute_fetchrow(query, channel_id)
        return result

    @classmethod
    async def subscribe_to_feed(cls, user_id: int, channel_id: int):
        """Subscribe to a new feed"""
        user_response = await cls.get_user(user_id)

        if user_response.is_error or user_response.data is None:
            return user_response

        feed_response = await cls.get_feed(channel_id)

        if feed_response.is_error or feed_response.data is None:
            return feed_response

        existing = await cls._execute_fetchrow(
            """
            SELECT *
            FROM users_feeds
            WHERE user_id = $1
              AND feed_id = $2
            """,
            user_id,
            channel_id,
        )

        if existing.success() and existing.data:
            msg = f"User {user_id} already subscribed to feed {channel_id}"
            logger.info(msg)
            return Response.error(status=ResponseStatus.ALREADY_SUBSCRIBED, message=msg)

        result = await cls._execute_fetchrow(
            """
            INSERT INTO users_feeds(user_id, feed_id)
            VALUES ($1, $2)
            RETURNING *
            """,
            user_id,
            channel_id,
        )
        return result

    @classmethod
    async def unsubscribe_from_feed(cls, user_id: int, channel_id: int):
        """Unsubscribe from a feed"""
        existing_subscription = await cls._execute_fetchrow(
            """
            SELECT user_id
            FROM users_feeds
            WHERE user_id = $1
              AND feed_id = $2;
            """,
            user_id,
            channel_id,
        )
        if existing_subscription.success() and not existing_subscription.data:
            msg = f"No subscription found for user {user_id} and feed {channel_id}"
            logger.info(msg)
            return Response.error(status=ResponseStatus.NO_SUBSCRIBTION, message=msg)

        if existing_subscription.success() and existing_subscription.data:
            query = """
                    DELETE
                    FROM users_feeds
                    WHERE user_id = $1
                      AND feed_id = $2;
                    """
            result = await cls._execute_execute(query, user_id, channel_id)
            return result

    @classmethod
    async def add_post_to_db(cls, post_id: int, text: str, channel_id: int, summary: str | None = None) -> Response:
        """Add a new post to the content table"""
        query = """
                INSERT INTO content(post_id, text, summary, channel_id)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (post_id, channel_id) DO NOTHING
                RETURNING post_id, channel_id
                """
        result = await cls._execute_fetchrow(query, post_id, text, summary, channel_id)
        return result

    @classmethod
    async def update_post_summary(cls, post_id: int, summary: str) -> Response:
        """Update summary for existing post in the content table"""
        query = """
                UPDATE content
                SET summary = $2
                WHERE post_id = $1
                RETURNING *
                """
        result = await cls._execute_fetchrow(query, post_id, summary)
        return result

    @classmethod
    async def get_post_summary(cls, channel_id: int, post_id: int) -> Response:
        query = """
                SELECT channel_id, post_id, summary
                FROM content
                WHERE post_id = $1
                  AND channel_id = $2
                  AND summary IS NOT NULL
                """
        result = await cls._execute_fetchrow(query, post_id, channel_id)
        return result
