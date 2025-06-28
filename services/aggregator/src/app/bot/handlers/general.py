import logging

from aiogram import Router  # type: ignore
from aiogram.filters import Command  # type: ignore
from aiogram.types import Message  # type: ignore

from ...core.registry import UserRegistry

logger = logging.getLogger("news_aggregator")

router = Router(name='general')


@router.message(Command("list"))
async def cmd_list(message: Message):
    """Handle /list command - show the user's subscribed feeds"""
    user_id = message.from_user.id

    try:
        user = await UserRegistry.get_or_create_user(user_id)
        feeds = user.get_user_feeds()

        if feeds:
            feed_list = "\n".join([f"• {feed.channel_name}" for feed in feeds.values()])
            await message.answer(f"Your subscriptions:\n\n{feed_list}")
        else:
            await message.answer("You dont have any subscriptions. Type /subscribe to add some.")
    except KeyError:
        await message.answer("Type /start to start the bot.")


@router.message(Command("upgrade_premium"))
async def cmd_upgrade_premium(message: Message):
    """Handle /upgrade_premium command - start the upgrade premium process"""
    user_id = message.from_user.id
    user = await UserRegistry.get_or_create_user(user_id)
    if user.is_premium:
        await message.answer("You already have premium subscription.")
        return

    await message.answer("Premium is not available yet.")

    # await user.upgrade_user_to_premium()


@router.message()
async def echo(message: Message):
    """Echo all other messages - fallback handler"""
    await message.answer(
        "🤔 I didn't understand that command.\n\n"
        "📋 <b>Available Commands:</b>\n\n"
        "🚀 /start - Start or restart the bot\n"
        "➕ /subscribe - Subscribe to a news feed\n"
        "📄 /list - View your subscribed feeds\n"
        "➖ /unsubscribe - Remove a feed subscription\n"
        "⏰ /notification_time - Set your daily news time\n"
        "🌍 /timezone - Change your timezone\n\n"
        "💡 <i>Tip: Just send a command to get started!</i>",
        parse_mode="HTML"
    )
