from aiogram.fsm.state import State, StatesGroup  # type: ignore


class FeedStates(StatesGroup):
    waiting_for_feed_name = State()
    confirm_unsubscribe = State()


class RegistrationStates(StatesGroup):
    waiting_for_location = State()
    waiting_for_timezone = State()
    waiting_for_notification_time = State()


class KeywordsStates(StatesGroup):
    waiting_for_keywords = State()
