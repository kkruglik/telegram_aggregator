import logging

from aiogram import Bot, Dispatcher  # type: ignore
from aiogram.fsm.storage.memory import MemoryStorage  # type: ignore

from .handlers import setup_handlers

logger = logging.getLogger("news_aggregator")


def init_bot(bot_token: str):
    bot = Bot(token=bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    main_router = setup_handlers()
    dp.include_routers(main_router)
    return bot, dp
