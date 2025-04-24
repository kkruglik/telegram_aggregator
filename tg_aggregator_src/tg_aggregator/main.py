import asyncio
import logging.config

from .bot.bot import init_bot
from .config import BOT_TOKEN, DATABASE_URL
from .core.registry import UserRegistry, FeedsRegistry
from .core.user import User
from .db.repository import DatabaseRepository
from .utils.utils import load_yaml

logger = logging.getLogger('news_aggregator')
logging.config.dictConfig(load_yaml('config/aggregator_logger.yaml'))


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
# TODO add loading summary to database, and when updating feed, check if summary is already there and skip it
# TODO add post from scraper to database, and when updating feed, check if post is already there and skip it


async def main():

    await DatabaseRepository.initialize(DATABASE_URL)

    bot, dp = init_bot(BOT_TOKEN)

    User.set_bot(bot)

    await FeedsRegistry.initialize()
    await UserRegistry.initialize()

    logger.info('Starting news aggregator')

    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
