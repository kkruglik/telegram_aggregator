import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from ...core.registry import FeedsRegistry, UserRegistry
from ...services.summarizer import summarizer_client

logger = logging.getLogger("news_aggregator")

router = Router(name="debug")


@router.message(Command("debug_trigger_feed_update"))
async def debug_trigger_feed_update(message: Message):
    user_id = message.from_user.id
    user = await UserRegistry.get_or_create_user(user_id)
    await message.answer("Running user full update!")

    await message.answer("Updating feeds")
    await user.update_users_feeds()

    await message.answer("Summarizing feeds!")
    await user.send_feed_update()

    await message.answer("Done!")
