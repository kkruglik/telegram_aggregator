import logging
from asyncio import sleep
from datetime import time

from aiogram import Router, types, F  # type: ignore
from aiogram.filters import CommandStart  # type: ignore
from aiogram.fsm.context import FSMContext  # type: ignore
from aiogram.types import Message  # type: ignore

from ..states import RegistrationStates
from ..utils import create_timezone_selection_keyboard, create_time_selection_keyboard
from ...core.registry import UserRegistry

logger = logging.getLogger("news_aggregator")

router = Router(name='registration')


@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    user = await UserRegistry.get_or_create_user(message.from_user.id)
    logger.info(f"New message from user {user}")

    greeting = f"👋 Hello, {message.from_user.first_name}!\n\n"

    if user.is_user_registered:
        commands_list = (
            "📋 <b>Available Commands:</b>\n\n"
            "➕ /subscribe - Subscribe to a news feed\n"
            "📄 /list - View your subscribed feeds\n"
            "➖ /unsubscribe - Remove a feed subscription\n"
            "⏰ /notification_time - Change your notification time\n"
            "🌍 /timezone - Change your timezone"
        )

        await message.answer(
            greeting +
            f"📰 Your personalized news feed is active and your notification time is set to {user.notification_time}.\n\n"
            f"{commands_list}",
            parse_mode="HTML"
        )
        return

    bot_description = (
        "📰 <b>Welcome to Evening Telegram Bot!</b>\n\n"
        "🤖 Get AI-summarized news from your favorite Telegram channels\n"
        "📅 Collects last 24 hours of posts and creates smart summaries\n"
        "🔗 Each summary includes a link to the original post\n"
        "⏰ Delivered once daily at your chosen time\n\n"
        "Let's get you set up in just a few steps!"
    )

    await message.answer(
        greeting + bot_description,
        parse_mode="HTML"
    )

    await sleep(0.3)

    await message.answer(
        "📍 <b>Select your timezone: </b>\n\n",
        reply_markup=create_timezone_selection_keyboard(),
        parse_mode="HTML"
    )

    await state.set_state(RegistrationStates.waiting_for_timezone)


@router.message(F.text == "/timezone")
async def change_timezone(message: Message, state: FSMContext):
    await message.answer(
        "📍 <b>Select your timezone: </b>\n\n",
        reply_markup=create_timezone_selection_keyboard(),
        parse_mode="HTML",
    )

    await state.set_state(RegistrationStates.waiting_for_timezone)


@router.message(F.text == "/notification_time")
async def change_notification_time(message: Message, state: FSMContext):
    await message.answer(
        "Please select your preferred notification time:",
        reply_markup=create_time_selection_keyboard(),
    )

    await state.set_state(RegistrationStates.waiting_for_notification_time)


@router.callback_query(RegistrationStates.waiting_for_timezone, F.data.startswith("__tz__"))
async def process_timezone(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user = await UserRegistry.get_or_create_user(user_id)

    try:
        selected_timezone = callback.data.split("__tz__")[1]
        await user.set_timezone(selected_timezone)

        await callback.message.edit_text(
            f"📍 <b>Timezone Selected:</b> {selected_timezone} ✅",
            parse_mode="HTML",
            reply_markup=None
        )

        await callback.answer()

        await callback.message.answer(
            "⏰ What time would you like to receive daily news updates?",
            reply_markup=create_time_selection_keyboard(),
        )

        await state.set_state(RegistrationStates.waiting_for_notification_time)

    except Exception as e:
        logger.error(f"Error processing timezone: {e}")
        await callback.answer("Error processing timezone. Please try again.")


@router.callback_query(RegistrationStates.waiting_for_notification_time, F.data.startswith("__time__"))
async def process_notification_time(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user = await UserRegistry.get_or_create_user(user_id)

    logger.info(f"Received notification time for user {user_id}")

    selected_time = callback.data.split("__time__")[1]

    hour, minute = map(int, selected_time.split(":"))
    notification_time = time(hour=hour, minute=minute)

    user.set_notification_time(notification_time)
    await user.save_user_to_database()
    UserRegistry.schedule_user_updates(user.id)

    await callback.message.edit_text(
        f"⏰ <b>Notification Time Selected:</b> {selected_time} ✅",
        parse_mode="HTML",
        reply_markup=None
    )

    await callback.answer()

    await callback.message.answer(
        f"🎉 <b>Registration Complete!</b>\n\n"
        f"✅ You'll receive your AI-summarized news digest at <b>{selected_time}</b> every day.\n\n"
        f"📰 Ready to get started? Use /subscribe to add your first news feed!",
        parse_mode="HTML"
    )

    await state.clear()
