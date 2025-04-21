import asyncio
import logging.config

from .bot.bot import start_bot, bot
from .config import DATABASE_URL
from .core.registry import UserRegistry, FeedsRegistry
from .core.user import User
from .db.repository import DatabaseRepository
from .utils.utils import load_yaml

logger = logging.getLogger('news_aggregator')
config = load_yaml('config/logger.yaml')
logging.config.dictConfig(config)


# TODO states of user are saved only locally with tg library
# TODO refactor commands
# TODO do i need a constant scraper.start()?
# TODO Added TTL-based cache expiration to prevent unbounded memory growth
# TODO Add sync when get user/feeds
# TODO what if was no messages during the period
# TODO add a documentation about bot logic, for now its really poorly documented
# TODO should i use microservices for summarization and scraping?
# TODO Telegram server says - Bad Request: message is too long
# TODO update system of clearing feed posts, for now i am just deleting send posts from feed


async def main():
    await DatabaseRepository.initialize(DATABASE_URL)

    User.set_bot(bot)

    await FeedsRegistry.initialize()
    await UserRegistry.initialize()

    logger.info('Starting news aggregator')
    await start_bot()


if __name__ == '__main__':
    asyncio.run(main())
