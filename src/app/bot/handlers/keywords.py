import logging

from aiogram import F, Router, types  # type: ignore
from aiogram.filters import Command  # type: ignore
from aiogram.fsm.context import FSMContext  # type: ignore
from aiogram.types import InaccessibleMessage, Message  # type: ignore

from ..states import KeywordsStates
from ..utils import create_keywords_actions_keyboard, create_keywords_feed_keyboard
from ...core.registry import UserRegistry

logger = logging.getLogger("news_aggregator")

router = Router(name="keywords")


def _format_keywords_message(channel_name: str, keywords: set) -> str:
    if not keywords:
        return f"📌 <b>{channel_name}</b>\n\nNo keyword filters set. All posts will be delivered."

    keywords_list = "\n".join(f"  • {kw}" for kw in sorted(keywords))
    return f"📌 <b>{channel_name}</b>\n\nActive keywords ({len(keywords)}):\n{keywords_list}"


@router.message(Command("keywords"))
async def cmd_keywords(message: Message):
    if message.from_user is None:
        logger.warning("cmd_keywords: from_user is None")
        return
    user_id = message.from_user.id
    logger.info(f"User {user_id} opened keyword management")
    user = await UserRegistry.get_or_create_user(user_id)
    feeds = user.get_user_feeds()

    if not feeds:
        logger.info(f"User {user_id} has no subscriptions for keyword management")
        await message.answer("You have no subscriptions. Use /subscribe to add channels.")
        return

    logger.info(f"User {user_id} has {len(feeds)} feeds for keyword management")
    keyboard = create_keywords_feed_keyboard(feeds, user.channel_filters)
    await message.answer("Select a channel to manage keyword filters:", reply_markup=keyboard)


@router.callback_query(
    F.data.startswith("__kw__")
    & ~F.data.startswith("__kw_add__")
    & ~F.data.startswith("__kw_clear__")
    & (F.data != "__kw_close__")
)
async def process_keywords_feed(callback_query: types.CallbackQuery):
    callback_data = callback_query.data
    callback_message = callback_query.message
    user_id = callback_query.from_user.id
    if callback_data is None or callback_message is None:
        logger.error(f"process_keywords_feed: callback data or message is None, user={user_id}")
        return
    if isinstance(callback_message, InaccessibleMessage):
        logger.error(
            f"process_keywords_feed: callback message is InaccessibleMessage, user={user_id}"
        )
        return

    channel_id = int(callback_data.replace("__kw__", ""))
    user = await UserRegistry.get_or_create_user(user_id)

    feed = user.user_feeds.get(channel_id)
    channel_name = feed.channel_name if feed else str(channel_id)
    current = user.channel_filters.get(channel_id, set())

    logger.info(
        f"User {user_id} viewing keywords for channel {channel_id} ({channel_name}): {current}"
    )

    await callback_message.edit_text(
        _format_keywords_message(channel_name, current),
        parse_mode="HTML",
        reply_markup=create_keywords_actions_keyboard(channel_id),
    )
    await callback_query.answer()


@router.callback_query(F.data.startswith("__kw_add__"))
async def process_keywords_add(callback_query: types.CallbackQuery, state: FSMContext):
    callback_data = callback_query.data
    callback_message = callback_query.message
    user_id = callback_query.from_user.id
    if callback_data is None or callback_message is None:
        logger.error(f"process_keywords_add: callback data or message is None, user={user_id}")
        return
    if isinstance(callback_message, InaccessibleMessage):
        logger.error(
            f"process_keywords_add: callback message is InaccessibleMessage, user={user_id}"
        )
        return

    channel_id = int(callback_data.replace("__kw_add__", ""))
    logger.info(f"User {user_id} adding keywords for channel {channel_id}")

    await state.update_data(channel_id=channel_id)
    await state.set_state(KeywordsStates.waiting_for_keywords)

    await callback_message.edit_text(
        "🔍 <b>Add keywords</b>\n\n"
        "Only posts that contain these words will be delivered to you.\n\n"
        "<i>Example:</i> <code>politics, economy, AI</code>\n\n"
        "New keywords will be added to existing ones.",
        parse_mode="HTML",
        reply_markup=None,
    )
    await callback_query.answer()


@router.callback_query(F.data == "__kw_close__")
async def process_keywords_close(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    callback_message = callback_query.message
    if callback_message is None or isinstance(callback_message, InaccessibleMessage):
        logger.error(
            f"process_keywords_close: callback message is None or InaccessibleMessage, user={user_id}"
        )
        return
    logger.info(f"User {user_id} closed keyword menu")
    await callback_message.delete()
    await callback_query.answer()


@router.callback_query(F.data.startswith("__kw_clear__"))
async def process_keywords_clear_callback(callback_query: types.CallbackQuery):
    callback_data = callback_query.data
    callback_message = callback_query.message
    user_id = callback_query.from_user.id
    if callback_data is None or callback_message is None:
        logger.error(
            f"process_keywords_clear_callback: callback data or message is None, user={user_id}"
        )
        return
    if isinstance(callback_message, InaccessibleMessage):
        logger.error(
            f"process_keywords_clear_callback: callback message is InaccessibleMessage, user={user_id}"
        )
        return

    channel_id = int(callback_data.replace("__kw_clear__", ""))
    user = await UserRegistry.get_or_create_user(user_id)

    feed = user.user_feeds.get(channel_id)
    channel_name = feed.channel_name if feed else str(channel_id)

    logger.info(f"User {user_id} clearing keywords for channel {channel_id} ({channel_name})")
    await user.clear_channel_filters(channel_id)
    logger.info(f"User {user_id} cleared keywords for channel {channel_id}")

    await callback_message.edit_text(
        _format_keywords_message(channel_name, set()),
        parse_mode="HTML",
        reply_markup=create_keywords_actions_keyboard(channel_id),
    )
    await callback_query.answer("Keywords cleared.")


@router.message(KeywordsStates.waiting_for_keywords, Command("skip"))
async def process_keywords_skip(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id if message.from_user else "unknown"
    logger.info(f"User {user_id} skipped adding keywords for channel {data.get('channel_id')}")
    await state.clear()
    await message.answer("No keywords added.")


@router.message(KeywordsStates.waiting_for_keywords)
async def process_keywords_input(message: Message, state: FSMContext):
    if message.from_user is None or message.text is None:
        logger.warning("process_keywords_input: from_user or text is None")
        return
    data = await state.get_data()
    channel_id = data["channel_id"]
    user_id = message.from_user.id
    user = await UserRegistry.get_or_create_user(user_id)

    new_keywords = {kw.strip().lower() for kw in message.text.split(",") if kw.strip()}

    if not new_keywords:
        logger.info(f"User {user_id} submitted empty keywords for channel {channel_id}")
        await message.answer("No valid keywords found. Please try again.")
        return

    logger.info(f"User {user_id} adding keywords {new_keywords} to channel {channel_id}")
    await user.add_channel_filters(channel_id, new_keywords)
    logger.info(f"User {user_id} added {len(new_keywords)} keywords to channel {channel_id}")

    feed = user.user_feeds.get(channel_id)
    channel_name = feed.channel_name if feed else str(channel_id)

    await state.clear()
    await message.answer(
        _format_keywords_message(channel_name, user.channel_filters[channel_id]),
        parse_mode="HTML",
    )
