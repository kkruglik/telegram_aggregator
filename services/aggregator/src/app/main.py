import asyncio
import logging.config
import os
from pathlib import Path

from .bot.bot import init_bot
from .config import initialize_config
from .core.registry import UserRegistry, FeedsRegistry
from .core.user import User
from .db.repository import DatabaseRepository
from .utils.utils import load_yaml, setup_cloud_logging, set_bot_commands

logger = logging.getLogger("news_aggregator")
logging.config.dictConfig(load_yaml("config/logger.yaml"))

setup_cloud_logging()


async def main():
    config_name = os.environ.get("CONFIG_NAME")

    assert config_name, "CONFIG_NAME environment variable not set"
    assert config_name.endswith(".yaml"), "CONFIG_NAME must end with .yaml"

    config_path = Path(__file__).resolve().parents[2] / "config" / config_name

    config = initialize_config(config_path)

    await DatabaseRepository.initialize(config.database.url)

    bot, dp = init_bot(config.bot.token)

    await set_bot_commands(bot)

    User.initialize(bot=bot)

    await FeedsRegistry.initialize(scraper_url=config.scraper.url)
    await UserRegistry.initialize()

    logger.info("Starting news aggregator")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
