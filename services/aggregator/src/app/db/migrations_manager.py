import os
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("news_aggregator")


class MigrationManager:
    """Manages database migrations using plain SQL files"""

    def __init__(self, migrations_dir="migrations/sql"):
        self.migrations_dir = Path(__file__).resolve().parent / migrations_dir
        self.migrations_dir.mkdir(parents=True, exist_ok=True)

    async def initialize_migrations_table(self, conn):
        """Create migrations table if it doesn't exist"""
        await conn.execute("""
                           CREATE TABLE IF NOT EXISTS schema_migrations
                           (
                               id         SERIAL PRIMARY KEY,
                               version    VARCHAR(255) NOT NULL UNIQUE,
                               name       VARCHAR(255) NOT NULL,
                               applied_at TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
                           )
                           """)

    async def get_applied_migrations(self, conn):
        """Get list of already applied migrations"""
        return set(m['version'] for m in await conn.fetch("SELECT version FROM schema_migrations ORDER BY id"))

    async def apply_migration(self, conn, version, name, sql_content):
        """Apply a single migration within a transaction"""
        try:
            async with conn.transaction():
                logger.info(f"Applying migration {version}: {name}")
                await conn.execute(sql_content)
                await conn.execute(
                    "INSERT INTO schema_migrations (version, name) VALUES ($1, $2)",
                    version, name
                )

            logger.info(f"Successfully applied migration {version}: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to apply migration {version}: {e}")
            return False

    async def run_migrations(self, pool):
        """Run all pending migrations"""
        try:
            logger.info("Running database migrations")
            logger.info(f"Migrations directory: {self.migrations_dir}")
            async with pool.acquire() as conn:
                await self.initialize_migrations_table(conn)
                applied_migrations = await self.get_applied_migrations(conn)

                logger.info(f"Found {len(applied_migrations)} applied migration(s)")
                logger.info(f"Applied migration(s): {applied_migrations}")

                migration_files = sorted([f for f in os.listdir(self.migrations_dir)
                                          if f.endswith('.sql')])

                logger.info(f"Found {len(migration_files)} migration(s)")
                logger.info(f"Migration(s): {migration_files}")

                applied_count = 0

                for migration_file in migration_files:
                    version = migration_file.split('_')[0]
                    name = '_'.join(migration_file.split('_')[1:]).replace('.sql', '')

                    logger.info(f"Processing migration {version}: {name}")

                    if version not in applied_migrations:
                        logger.info(f"Migration {version} not applied yet")
                        with open(os.path.join(self.migrations_dir, migration_file)) as f:
                            migration_sql = f.read()

                        success = await self.apply_migration(conn, version, name, migration_sql)
                        if success:
                            applied_count += 1

            if applied_count > 0:
                logger.info(f"Applied {applied_count} migration(s)")
            else:
                logger.info("No new migrations to apply")

        except Exception as e:
            logger.error(f"Error running database migrations: {e}")
            raise

    def create_migration(self, name):
        """Create a new migration file"""
        try:
            clean_name = name.lower().replace(' ', '_').replace('-', '_')
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"{timestamp}_{clean_name}.sql"
            filepath = self.migrations_dir / filename

            with open(filepath, "w") as f:
                f.write(f"-- Migration: {name}\n")
                f.write(f"-- Version: {timestamp}\n")
                f.write(f"-- Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("-- Write your SQL migration here\n\n")

                f.write("-- Example operations:\n")
                f.write("-- CREATE TABLE new_table (...)\n")
                f.write("-- ALTER TABLE existing_table ADD COLUMN new_column VARCHAR(100)\n")
                f.write("-- ALTER TABLE existing_table DROP COLUMN old_column\n")

            logger.info(f"Created migration file: {filepath}")
            print(f"Created migration file: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error creating migration file: {e}")
            raise
