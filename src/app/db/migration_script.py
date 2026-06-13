import asyncio

from .repository import DatabaseRepository


async def create_migration():
    migration_name = input("Enter migration name: ")
    DatabaseRepository.create_migration(migration_name)


if __name__ == "__main__":
    asyncio.run(create_migration())
