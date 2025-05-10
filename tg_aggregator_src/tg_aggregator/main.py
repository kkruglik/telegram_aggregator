import asyncio
import logging.config
import os
from pathlib import Path

from google import genai

from .bot.bot import init_bot
from .config import initialize_config
from .core.feed import TelegramFeed
from .core.registry import UserRegistry, FeedsRegistry
from .core.user import User
from .db.repository import DatabaseRepository
from .utils.utils import load_yaml, setup_cloud_logging

logger = logging.getLogger("news_aggregator")
logging.config.dictConfig(load_yaml("config/aggregator/logger.yaml"))

setup_cloud_logging()


async def main():
    config_name = os.environ.get("CONFIG_NAME")

    assert config_name, "CONFIG_NAME environment variable not set"
    assert config_name.endswith(".yaml"), "CONFIG_NAME must end with .yaml"

    config_path = Path(__file__).resolve().parents[2] / "config" / "aggregator" / config_name

    config = initialize_config(config_path)

    client = genai.Client(api_key=config.gemini.token)

    await DatabaseRepository.initialize(config.database.url)

    bot, dp = init_bot(config.bot.token)

    User.initialize(bot=bot)
    TelegramFeed.initialize(client=client, scraper_url=config.scraper.url)

    await FeedsRegistry.initialize(scraper_url=config.scraper.url)
    await UserRegistry.initialize()

    logger.info("Starting news aggregator")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
