import logging

from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InaccessibleMessage, Message

from ...core.enums import ResponseStatus
from ...core.registry import FeedsRegistry, UserRegistry
from ..states import FeedStates, KeywordsStates
from ..utils import create_unsubscribe_keyboard

logger = logging.getLogger("news_aggregator")

router = Router(name="subscription")


@router.message(Command("subscribe"))
async def subscribe(message: Message, state: FSMContext):
    if message.from_user is None:
        logger.warning("subscribe: from_user is None")
        return
    user_id = message.from_user.id
    logger.info(f"User {user_id} started subscription flow")
    await message.answer("Send channel name in format @channel_name or https://t.me/channel_name")
    await state.set_state(FeedStates.waiting_for_feed_name)


@router.message(FeedStates.waiting_for_feed_name)
async def process_feed_name(message: Message, state: FSMContext):
    """Process the feed name provided by the user"""
    feed_name = message.text.strip() if message.text else None

    if not feed_name:
        await message.answer(
            "Send channel name in format @channel_name or https://t.me/channel_name"
        )
        return

    user_id = message.from_user.id if message.from_user else None

    if user_id is None:
        logger.warning("process_feed_name: from_user is None")
        await message.answer("Unknown error. Please try again.")
        return

    logger.info(f"User {user_id} subscribing to {feed_name!r}")
    user = await UserRegistry.get_or_create_user(user_id)
    feed = await FeedsRegistry.create_or_get_feed(feed_name)

    if feed is None:
        logger.warning(f"User {user_id}: feed {feed_name!r} not found")
        await message.answer(
            "❌ Channel not found. Please try again. "
            "Send channel name in format @channel_name or https://t.me/channel_name"
        )
        return

    result = await user.subscribe(feed)

    match result.status:
        case ResponseStatus.OK:
            logger.info(
                f"User {user_id} subscribed to {feed.channel_name!r} (id={feed.channel_id})"
            )
            await message.answer(
                f"✅ Subscribed to <b>{feed.channel_name}</b>\n\n"
                "🔍 <b>Set keyword filters</b>\n\n"
                "Only posts that contain these words will be delivered to you.\n\n"
                "<i>Example:</i> <code>politics, economy, AI</code>\n\n"
                "Send keywords separated by commas, or /skip to receive all posts.",
                parse_mode="HTML",
            )
            await state.update_data(channel_id=feed.channel_id)
            await state.set_state(KeywordsStates.waiting_for_keywords)
            return
        case ResponseStatus.LIMIT_REACHED:
            logger.info(f"User {user_id} hit subscription limit")
            await message.answer(
                "❌ You've reached the limit of feeds. Upgrade to premium to add more feeds!"
            )
        case ResponseStatus.ALREADY_SUBSCRIBED:
            logger.info(f"User {user_id} already subscribed to {feed_name!r}")
            await message.answer(f"ℹ️ You're already subscribed to {feed_name}.")
        case ResponseStatus.DATABASE_ERROR:
            logger.error(f"User {user_id}: database error subscribing to {feed_name!r}")
            await message.answer("❌ Sorry, there was a technical issue. Please try again later.")
        case _:
            logger.error(
                f"User {user_id}: unexpected status {result.status!r} subscribing to {feed_name!r}"
            )
            await message.answer("❌ An unexpected error occurred. Please try again.")

    await state.clear()  # only reached on non-OK cases


@router.message(Command("unsubscribe"))
async def cmd_unsubscribe(message: Message, state: FSMContext):
    """Handle /unsubscribe command - start the unsubscription process"""
    # TODO state is not used here
    # TODO fix unsubscribe logic, how convert channel names to ids?

    user_id = message.from_user.id if message.from_user else None

    if user_id is None:
        logger.warning("cmd_unsubscribe: from_user is None")
        await message.answer("Unknown error. Please try again.")
        return

    logger.info(f"User {user_id} started unsubscription flow")

    try:
        user = await UserRegistry.get_or_create_user(user_id)
        feeds = user.get_user_feeds()

        if not feeds:
            logger.info(f"User {user_id} has no subscriptions to unsubscribe from")
            await message.answer("You dont have any subscriptions. Type /subscribe to add some.")
            return

        logger.info(f"User {user_id} has {len(feeds)} subscriptions, showing unsubscribe keyboard")
        unsubscribe_keyboard = create_unsubscribe_keyboard(feeds)
        await message.answer("Select channel to unsubscribe:", reply_markup=unsubscribe_keyboard)
    except KeyError:
        logger.warning(f"User {user_id} not found in registry during unsubscribe")
        await message.answer("Enter /start to start the bot.")


@router.callback_query(F.data.startswith("__unsub__"))
async def process_unsubscribe_callback(callback_query: types.CallbackQuery):
    """Process the unsubscription callback"""
    callback_message = callback_query.message
    callback_data = callback_query.data
    user_id = callback_query.from_user.id

    if callback_data is None or callback_message is None:
        logger.error(
            f"process_unsubscribe_callback: callback data or message is None, user={user_id}"
        )
        await callback_query.answer()
        return

    if isinstance(callback_message, InaccessibleMessage):
        logger.error(
            f"process_unsubscribe_callback: callback message is InaccessibleMessage, user={user_id}"
        )
        await callback_query.answer()
        return

    try:
        feed_id = int(callback_data.replace("__unsub__", ""))
        logger.info(f"User {user_id} unsubscribing from feed {feed_id}")
        user = await UserRegistry.get_or_create_user(user_id)
        result = await user.unsubscribe(feed_id)

        match result.status:
            case ResponseStatus.OK:
                logger.info(f"User {user_id} unsubscribed from feed {feed_id}")
                await callback_message.edit_text(
                    "✅ You successfully unsubscribed from the channel.\n\n"
                    "Use /subscribe to add new feeds or /list to see your remaining subscriptions.",
                    parse_mode="HTML",
                    reply_markup=None,
                )
                FeedsRegistry.release_feed(feed_id)

            case ResponseStatus.UNKNOWN_ERROR:
                logger.error(f"User {user_id}: unknown error unsubscribing from feed {feed_id}")
                await callback_message.edit_text(
                    "❌ Sorry, there was a technical issue. Please try again later.",
                    parse_mode="HTML",
                    reply_markup=None,
                )
            case _:
                logger.error(
                    f"User {user_id}: unexpected status {result.status!r} unsubscribing from feed {feed_id}"
                )
                await callback_message.edit_text(
                    "❌ Sorry, there was a technical issue. Please try again later.",
                    parse_mode="HTML",
                    reply_markup=None,
                )

        await callback_query.answer()

    except ValueError:
        logger.warning(
            f"User {user_id}: invalid feed_id in unsubscribe callback data {callback_data!r}"
        )
        await callback_query.answer("Invalid channel selection.")
    except Exception as e:
        logger.error(f"User {user_id}: error processing unsubscribe: {e}", exc_info=True)
        await callback_message.answer("❌ Unknown error. Try again later.")
        await callback_query.answer("Error occurred. Please try again.")
