import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from .handlers.commands import router as commands_router
from ..config import BOT_TOKEN

bot = Bot(token=BOT_TOKEN)

logger = logging.getLogger('news_aggregator')


async def start_bot():
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.include_routers(commands_router)
    await dp.start_polling(bot)
