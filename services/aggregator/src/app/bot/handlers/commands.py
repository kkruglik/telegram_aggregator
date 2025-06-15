import logging
from datetime import time

from aiogram import Router, types, F  # type: ignore
from aiogram.filters import Command, CommandStart  # type: ignore
from aiogram.fsm.context import FSMContext  # type: ignore
from aiogram.fsm.state import State, StatesGroup  # type: ignore
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton  # type: ignore
from aiogram.utils.keyboard import InlineKeyboardBuilder  # type: ignore

from ...core.enums import ResponseStatus
from ...core.registry import UserRegistry, FeedsRegistry

logger = logging.getLogger("news_aggregator")

router = Router()


class FeedStates(StatesGroup):
    waiting_for_feed_name = State()
    confirm_unsubscribe = State()


class RegistrationStates(StatesGroup):
    waiting_for_location = State()
    waiting_for_notification_time = State()


def create_time_selection_keyboard():
    builder = InlineKeyboardBuilder()
    hours = [
        "06:00",
        "07:00",
        "08:00",
        "09:00",
        "10:00",
        "11:00",
        "12:00",
        "13:00",
        "14:00",
        "15:00",
        "16:00",
        "17:00",
        "18:00",
        "19:00",
        "20:00",
        "21:00",
        "22:00",
    ]

    for hour in hours:
        builder.button(text=hour, callback_data=f"time:{hour}")

    builder.adjust(3)
    return builder.as_markup()


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
            "⏰ /notification_time - Change your notification time"
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
        "🔔 Subscribe to multiple channels and receive a personalized daily digest\n"
        "⏰ Get all your news in one convenient message at your preferred time\n"
        "🌍 Stay informed with content tailored to your timezone\n\n"
        "Let's get you set up in just a few steps!"
    )

    location_message = (
        "📍 <b>Location for Timezone (Optional)</b>\n\n"
        "🔐 <b>Privacy-safe</b>: We only use your location to calculate timezone - no data is stored or tracked.\n\n"
        "⏭️ <b>Skip available</b>: Default timezone is EET (Eastern European Time)\n"
        "🏙️ <i>Cities: Helsinki, Athens, Cairo, Kiev, Bucharest, Sofia</i>"
    )

    location_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Share My Location", request_location=True)],
            [KeyboardButton(text="⏭️ Skip - Use EET Default")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await message.answer(
        greeting + bot_description + "\n\n" + location_message,
        reply_markup=location_keyboard,
        parse_mode="HTML"
    )

    await state.set_state(RegistrationStates.waiting_for_location)


@router.message(F.text == "/location")
async def change_location(message: Message, state: FSMContext):
    location_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Share My Location", request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await message.answer(
        "Please share your updated location. This information need to determine your timezone.",
        reply_markup=location_keyboard,
    )

    await state.set_state(RegistrationStates.waiting_for_location)


@router.message(F.text == "/notification_time")
async def change_notification_time(message: Message, state: FSMContext):
    await message.answer(
        "Please select your preferred notification time:",
        reply_markup=create_time_selection_keyboard(),
    )

    await state.set_state(RegistrationStates.waiting_for_notification_time)


@router.message(RegistrationStates.waiting_for_location)
async def process_location(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user = await UserRegistry.get_or_create_user(user_id)

    if message.location:
        lat = message.location.latitude
        lng = message.location.longitude
        await user.set_timezone(lat, lng)

        await message.answer(
            f"Thanks for sharing your location! Your timezone is set to {user.timezone}."
        )
    elif message.text == "⏭️ Skip - Use EET Default":
        await message.answer("Location skipped. Your default timezone will be EET.")
    else:
        await message.answer("Please use the buttons to share your location or skip this step.")
        return  # Don't proceed to next step

    # Move to notification time selection
    await message.answer(
        "What time would you like to receive daily news updates?",
        reply_markup=create_time_selection_keyboard(),
    )

    await state.set_state(RegistrationStates.waiting_for_notification_time)


@router.callback_query(RegistrationStates.waiting_for_notification_time, F.data.startswith("time:"))
async def process_notification_time(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user = await UserRegistry.get_or_create_user(user_id)

    logger.info(f"Received notification time for user {user_id}")

    selected_time = callback.data.split("time:")[1]

    hour, minute = map(int, selected_time.split(":"))
    notification_time = time(hour=hour, minute=minute)

    user.set_notification_time(notification_time)
    await user.save_user_to_database()
    UserRegistry.schedule_user_updates(user.id)

    await callback.message.answer(
        f"Great! Your registration is complete. You'll receive news updates at {selected_time} every day.\n\n"
        f"Use /subscribe to add some feeds"
    )

    await callback.answer()
    await state.clear()


@router.message(Command("subscribe"))
async def subscribe(message: Message, state: FSMContext):
    await message.answer("Send channel name in format @channel_name")
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
            await message.answer("У вас нет текущих подписок.")
            return

        # Create keyboard with feed options - this is the fixed part
        buttons = []
        for feed in feeds.values():
            channel_name = feed.channel_name
            buttons.append(
                [
                    types.InlineKeyboardButton(
                        text=channel_name, callback_data=f"unsub_{feed.channel_id}"
                    )
                ]
            )

        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

        await message.answer("Select channel to unsubscribe:", reply_markup=keyboard)
    except KeyError:
        await message.answer("Enter /start to start the bot.")


@router.callback_query(F.data.startswith("unsub_"))
async def process_unsubscribe_callback(callback_query: types.CallbackQuery):
    """Process the unsubscription callback"""

    feed_id = int(callback_query.data.replace("unsub_", ""))
    user_id = callback_query.from_user.id

    try:
        user = await UserRegistry.get_or_create_user(user_id)
        await user.unsubscribe(feed_id)
        FeedsRegistry.release_feed(feed_id)

        await callback_query.message.answer("✅ You successfully unsubscribed from channel.")
        await callback_query.answer()

        await callback_query.message.edit_reply_markup(
            reply_markup=None
        )  # This replaces bot.edit_message_reply_markup
    except KeyError:
        await callback_query.message.answer("Unknown error. Try again later.")
        await callback_query.answer()  # This replaces bot.answer_callback_query


@router.message(Command("upgrade_premium"))
async def cmd_upgrade_premium(message: Message):
    """Handle /upgrade_premium command - start the upgrade premium process"""
    user_id = message.from_user.id
    user = await UserRegistry.get_or_create_user(user_id)
    if user.is_premium:
        await message.answer("You already have premium subscription.")
        return

    await user.upgrade_user_to_premium()


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
        "⏰ /notification_time - Set your daily news time\n\n"
        "💡 <i>Tip: Just send a command to get started!</i>",
        parse_mode="HTML"
    )
