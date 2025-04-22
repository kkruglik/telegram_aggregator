import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from .handlers.commands import router as commands_router

logger = logging.getLogger('news_aggregator')


def init_bot(bot_token: str):
    bot = Bot(token=bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.include_routers(commands_router)
    return bot, dp
