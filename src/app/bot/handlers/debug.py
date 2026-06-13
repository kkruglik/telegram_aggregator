import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from ...core.registry import UserRegistry

logger = logging.getLogger("news_aggregator")

router = Router(name="debug")


@router.message(Command("debug_trigger_feed_update"))
async def debug_trigger_feed_update(message: Message):
    if message.from_user is None:
        logger.warning("debug_trigger_feed_update: from_user is None")
        return
    user_id = message.from_user.id
    logger.info(f"User {user_id} triggered debug feed update")
    user = await UserRegistry.get_or_create_user(user_id)
    await message.answer("Running user full update!")

    logger.info(f"User {user_id}: updating feeds")
    await message.answer("Updating feeds")
    await user.update_users_feeds()

    logger.info(f"User {user_id}: sending feed update")
    await message.answer("Summarizing feeds!")
    await user.send_feed_update()

    logger.info(f"User {user_id}: debug update complete")
    await message.answer("Done!")
