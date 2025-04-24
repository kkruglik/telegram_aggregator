import logging
from datetime import time

from aiogram import Router, types, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ...core.registry import UserRegistry, FeedsRegistry

logger = logging.getLogger('news_aggregator')

router = Router()


class FeedStates(StatesGroup):
    waiting_for_feed_name = State()
    confirm_unsubscribe = State()


class RegistrationStates(StatesGroup):
    waiting_for_location = State()
    waiting_for_notification_time = State()


def create_time_selection_keyboard():
    builder = InlineKeyboardBuilder()
    hours = ["06:00", "07:00", "08:00", "09:00", "10:00", "11:00",
             "12:00", "14:00", "17:30", "18:00", "20:00", "22:00"]

    for hour in hours:
        builder.button(text=hour, callback_data=f"time:{hour}")

    builder.adjust(3)  # 3 buttons per row
    return builder.as_markup()


@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    user = await UserRegistry.get_or_create_user(message.from_user.id)
    logger.info(f'New message from user {user}')

    if user.is_user_registered:
        await message.answer(f"Welcome back! Your notification time is set to {user.notification_time}.")
        return

    location_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Share My Location", request_location=True)],
            [KeyboardButton(text="Skip Location")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.answer(
        "Please share your location so we can provide news relevant to your timezone.",
        reply_markup=location_keyboard
    )

    await state.set_state(RegistrationStates.waiting_for_location)


@router.message(F.text == "/location")
async def change_location(message: Message, state: FSMContext):
    location_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Share My Location", request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.answer(
        "Please share your updated location. This information need to determine your timezone.",
        reply_markup=location_keyboard
    )

    await state.set_state(RegistrationStates.waiting_for_location)


@router.message(F.text == "/notification_time")
async def change_notification_time(message: Message, state: FSMContext):
    await message.answer(
        "Please select your preferred notification time:",
        reply_markup=create_time_selection_keyboard()
    )

    await state.set_state(RegistrationStates.waiting_for_notification_time)


@router.message(RegistrationStates.waiting_for_location)
async def process_location(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user = await UserRegistry.get_or_create_user(user_id)

    if message.location:
        lat = message.location.latitude
        lng = message.location.longitude
        user.set_timezone(lat, lng)

        await message.answer(f"Thanks for sharing your location! Your timezone is set to {user.timezone}.")
    elif message.text == "Skip Location":
        await message.answer("Location skipped. Your default timezone will be EET.")
    else:
        await message.answer("Please use the buttons to share your location or skip this step.")
        return  # Don't proceed to next step

    # Move to notification time selection
    await message.answer(
        "What time would you like to receive daily news updates?",
        reply_markup=create_time_selection_keyboard()
    )

    await state.set_state(RegistrationStates.waiting_for_notification_time)


@router.callback_query(RegistrationStates.waiting_for_notification_time, F.data.startswith("time:"))
async def process_notification_time(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user = await UserRegistry.get_or_create_user(user_id)

    logger.info(f'Callback data: {callback.data}')

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


@router.message(Command('subscribe'))
async def subscribe(message: Message, state: FSMContext):
    await message.answer("Send channel name in format @channel_name")
    await state.set_state(FeedStates.waiting_for_feed_name)


@router.message(FeedStates.waiting_for_feed_name)
async def process_feed_name(message: Message, state: FSMContext):
    """Process the feed name provided by the user"""
    feed_name = message.text.strip()

    if not feed_name:
        await message.answer("Send channel name in format @channel_name")
        return

    user_id = message.from_user.id
    user = await UserRegistry.get_or_create_user(user_id)
    feed = await FeedsRegistry.create_or_get_feed(feed_name)

    if feed.channel_id in user._user_feeds:
        await message.answer(f"You already subscribed for this channel: {feed_name}.")
    else:
        await user.subscribe(feed)
        await message.answer(f"✅ You successfully subscribed for this channel: {feed_name}!")

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
            await message.answer(
                "You dont have any subscriptions. Type /subscribe to add some.")
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
            buttons.append([types.InlineKeyboardButton(
                text=channel_name,
                callback_data=f"unsub_{feed.channel_id}"
            )])

        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

        await message.answer("Select channel to unsubscribe:", reply_markup=keyboard)
    except KeyError:
        await message.answer("Enter /start to start the bot.")


@router.callback_query(F.data.startswith("unsub_"))
async def process_unsubscribe_callback(callback_query: types.CallbackQuery):
    """Process the unsubscription callback"""

    feed_id = int(callback_query.data.replace('unsub_', ''))
    user_id = callback_query.from_user.id

    try:
        user = await UserRegistry.get_or_create_user(user_id)
        await user.unsubscribe(feed_id)
        FeedsRegistry.release_feed(feed_id)

        await callback_query.message.answer(f"✅ You successfully unsubscribed from channel.")
        await callback_query.answer()

        await callback_query.message.edit_reply_markup(reply_markup=None)  # This replaces bot.edit_message_reply_markup
    except KeyError:
        await callback_query.message.answer("Unknown error. Try again later.")
        await callback_query.answer()  # This replaces bot.answer_callback_query


@router.message()
async def echo(message: Message):
    """Echo all other messages - fallback handler"""
    await message.answer(
        "I didn't understand that command. Try using one of these:\n\n"
        "/start - Start the bot\n"
        "/subscribe - Subscribe to a feed\n"
        "/list - List your subscribed feeds\n"
        "/unsubscribe - Unsubscribe from a feed\n"
        "/notification_time - Change your notification time\n"
    )
