import asyncio
import logging.config

from .bot.bot import init_bot
from .config import config
from .core.registry import UserRegistry, FeedsRegistry
from .core.user import User
from .db.repository import DatabaseRepository
from .utils.utils import load_yaml, setup_cloud_logging, set_bot_commands

logger = logging.getLogger("news_aggregator")
logging.config.dictConfig(load_yaml("config/logger.yaml"))

setup_cloud_logging()


async def main():
    await DatabaseRepository.initialize(config.database.url)

    bot, dp = init_bot(config.bot.token)

    await set_bot_commands(bot)

    User.initialize(bot=bot)

    await FeedsRegistry.initialize()
    await UserRegistry.initialize()

    logger.info("Starting news aggregator")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
