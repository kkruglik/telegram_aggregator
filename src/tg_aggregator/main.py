import asyncio
import logging.config

from .bot.bot import start_bot, bot
from .core.registry import UserRegistry, FeedsRegistry
from .core.feed import TelegramFeed
from .core.user import User
from .services.telethon_scraper import TelegramScraper
from .utils.utils import load_yaml
from .config import API_ID, API_HASH, DATABASE_URL
from .db.repository import DatabaseRepository

logger = logging.getLogger('news_aggregator')
config = load_yaml('config/logger.yaml')
logging.config.dictConfig(config)


# TODO states of user are saved only locally with tg library
# TODO refactor commands
# TODO do i need a constant scraper.start()?
# TODO Added TTL-based cache expiration to prevent unbounded memory growth
# TODO Add sync when get user/feeds
# Todo add a normal prompt


async def main():
    scraper = TelegramScraper(
        api_id=API_ID,
        api_hash=API_HASH,
    )
    await DatabaseRepository.initialize(DATABASE_URL)

    TelegramFeed.set_scraper_service(scraper)

    User.set_bot(bot)

    await FeedsRegistry.initialize(scraper)
    await UserRegistry.initialize()

    logger.info('Starting news aggregator')
    await start_bot()


if __name__ == '__main__':
    asyncio.run(main())
