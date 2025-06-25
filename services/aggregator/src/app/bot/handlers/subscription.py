import logging

from aiogram import Router, types, F  # type: ignore
from aiogram.filters import Command # type: ignore
from aiogram.fsm.context import FSMContext  # type: ignore
from aiogram.types import Message  # type: ignore

from ..states import FeedStates
from ..utils import create_unsubscribe_keyboard
from ...core.enums import ResponseStatus
from ...core.registry import UserRegistry, FeedsRegistry

logger = logging.getLogger("news_aggregator")

router = Router(name='subscription')


@router.message(Command("subscribe"))
async def subscribe(message: Message, state: FSMContext):
    await message.answer(
        "Send channel name in format @channel_name or https://t.me/channel_name")
    await state.set_state(FeedStates.waiting_for_feed_name)


@router.message(FeedStates.waiting_for_feed_name)
async def process_feed_name(message: Message, state: FSMContext):
    """Process the feed name provided by the user"""
    feed_name = message.text.strip()

    if not feed_name:
        await message.answer("Send channel name in format @channel_name or https://t.me/channel_name")
        return

    user_id = message.from_user.id
    user = await UserRegistry.get_or_create_user(user_id)
    feed = await FeedsRegistry.create_or_get_feed(feed_name)

    if feed is None:
        await message.answer("❌ Channel not found. Please try again. "
                             "Send channel name in format @channel_name or https://t.me/channel_name")
        return

    result = await user.subscribe(feed)

    match result.status:
        case ResponseStatus.OK:
            await message.answer(f"✅ You successfully subscribed for this channel: {feed.channel_name}!")
        case ResponseStatus.LIMIT_REACHED:
            await message.answer(
                "❌ You've reached the limit of feeds. Upgrade to premium to add more feeds!"
            )
        case ResponseStatus.ALREADY_SUBSCRIBED:
            await message.answer(f"ℹ️ You're already subscribed to {feed_name}.")
        case ResponseStatus.DATABASE_ERROR:
            await message.answer("❌ Sorry, there was a technical issue. Please try again later.")
        case _:
            await message.answer("❌ An unexpected error occurred. Please try again.")

    await state.clear()


@router.message(Command("unsubscribe"))
async def cmd_unsubscribe(message: Message, state: FSMContext):
    """Handle /unsubscribe command - start the unsubscription process"""
    # TODO state is not used here
    # TODO fix unsubscribe logic, how convert channel names to ids?

    user_id = message.from_user.id

    try:
        user = await UserRegistry.get_or_create_user(user_id)
        feeds = user.get_user_feeds()

        if not feeds:
            await message.answer("You dont have any subscriptions. Type /subscribe to add some.")
            return

        unsubscribe_keyboard = create_unsubscribe_keyboard(feeds)
        await message.answer("Select channel to unsubscribe:", reply_markup=unsubscribe_keyboard)
    except KeyError:
        await message.answer("Enter /start to start the bot.")


@router.callback_query(F.data.startswith("__unsub__"))
async def process_unsubscribe_callback(callback_query: types.CallbackQuery):
    """Process the unsubscription callback"""
    try:
        feed_id = int(callback_query.data.replace("__unsub__", ""))
        user_id = callback_query.from_user.id
        user = await UserRegistry.get_or_create_user(user_id)
        result = await user.unsubscribe(feed_id)

        match result.status:
            case ResponseStatus.OK:
                await callback_query.message.edit_text(
                    "✅ You successfully unsubscribed from the channel.\n\n"
                    "Use /subscribe to add new feeds or /list to see your remaining subscriptions.",
                    parse_mode="HTML",
                    reply_markup=None
                )
                FeedsRegistry.release_feed(feed_id)

            case ResponseStatus.UNKNOWN_ERROR:
                await callback_query.message.edit_text(
                    "❌ Sorry, there was a technical issue. Please try again later.",
                    parse_mode="HTML",
                    reply_markup=None
                )
            case _:
                await callback_query.message.edit_text(
                    "❌ Sorry, there was a technical issue. Please try again later.",
                    parse_mode="HTML",
                    reply_markup=None
                )

        await callback_query.answer()

    except ValueError:
        await callback_query.answer("Invalid channel selection.")
    except Exception as e:
        logger.error(f"Error processing unsubscribe: {e}")
        await callback_query.message.answer("❌ Unknown error. Try again later.")
        await callback_query.answer("Error occurred. Please try again.")
