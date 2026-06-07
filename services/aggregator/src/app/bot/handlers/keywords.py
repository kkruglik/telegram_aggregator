import logging

from aiogram import Router, types, F  # type: ignore
from aiogram.filters import Command  # type: ignore
from aiogram.fsm.context import FSMContext  # type: ignore
from aiogram.types import Message  # type: ignore

from ..states import KeywordsStates
from ..utils import create_keywords_feed_keyboard, create_keywords_actions_keyboard
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
    user_id = message.from_user.id
    user = await UserRegistry.get_or_create_user(user_id)
    feeds = user.get_user_feeds()

    if not feeds:
        await message.answer("You have no subscriptions. Use /subscribe to add channels.")
        return

    keyboard = create_keywords_feed_keyboard(feeds, user.channel_filters)
    await message.answer("Select a channel to manage keyword filters:", reply_markup=keyboard)


@router.callback_query(
    F.data.startswith("__kw__")
    & ~F.data.startswith("__kw_add__")
    & ~F.data.startswith("__kw_clear__")
    & (F.data != "__kw_close__")
)
async def process_keywords_feed(callback_query: types.CallbackQuery):
    channel_id = int(callback_query.data.replace("__kw__", ""))
    user_id = callback_query.from_user.id
    user = await UserRegistry.get_or_create_user(user_id)

    feed = user.user_feeds.get(channel_id)
    channel_name = feed.channel_name if feed else str(channel_id)
    current = user.channel_filters.get(channel_id, set())

    logger.info(f"User {user_id} viewing keywords for channel {channel_id}: {current}")

    await callback_query.message.edit_text(
        _format_keywords_message(channel_name, current),
        parse_mode="HTML",
        reply_markup=create_keywords_actions_keyboard(channel_id),
    )
    await callback_query.answer()


@router.callback_query(F.data.startswith("__kw_add__"))
async def process_keywords_add(callback_query: types.CallbackQuery, state: FSMContext):
    channel_id = int(callback_query.data.replace("__kw_add__", ""))
    user_id = callback_query.from_user.id

    logger.info(f"User {user_id} adding keywords for channel {channel_id}")

    await state.update_data(channel_id=channel_id)
    await state.set_state(KeywordsStates.waiting_for_keywords)

    await callback_query.message.edit_text(
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
    await callback_query.message.delete()
    await callback_query.answer()


@router.callback_query(F.data.startswith("__kw_clear__"))
async def process_keywords_clear_callback(callback_query: types.CallbackQuery):
    channel_id = int(callback_query.data.replace("__kw_clear__", ""))
    user_id = callback_query.from_user.id
    user = await UserRegistry.get_or_create_user(user_id)

    feed = user.user_feeds.get(channel_id)
    channel_name = feed.channel_name if feed else str(channel_id)

    await user.clear_channel_filters(channel_id)

    await callback_query.message.edit_text(
        _format_keywords_message(channel_name, set()),
        parse_mode="HTML",
        reply_markup=create_keywords_actions_keyboard(channel_id),
    )
    await callback_query.answer("Keywords cleared.")


@router.message(KeywordsStates.waiting_for_keywords, Command("skip"))
async def process_keywords_skip(message: Message, state: FSMContext):
    data = await state.get_data()
    logger.info(
        f"User {message.from_user.id} skipped adding keywords for channel {data.get('channel_id')}"
    )
    await state.clear()
    await message.answer("No keywords added.")


@router.message(KeywordsStates.waiting_for_keywords)
async def process_keywords_input(message: Message, state: FSMContext):
    data = await state.get_data()
    channel_id = data["channel_id"]
    user = await UserRegistry.get_or_create_user(message.from_user.id)

    new_keywords = {kw.strip().lower() for kw in message.text.split(",") if kw.strip()}

    if not new_keywords:
        await message.answer("No valid keywords found. Please try again.")
        return

    await user.add_channel_filters(channel_id, new_keywords)

    feed = user.user_feeds.get(channel_id)
    channel_name = feed.channel_name if feed else str(channel_id)

    await state.clear()
    await message.answer(
        _format_keywords_message(channel_name, user.channel_filters[channel_id]),
        parse_mode="HTML",
    )
