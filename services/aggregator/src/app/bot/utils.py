from aiogram.utils.keyboard import InlineKeyboardBuilder  # type: ignore


def create_time_selection_keyboard():
    builder = InlineKeyboardBuilder()

    hours = [f"{i}:00".zfill(2) for i in range(0, 24)]

    for hour in hours:
        builder.button(text=hour, callback_data=f"__time__{hour}")

    builder.adjust(3)
    return builder.as_markup()


def create_timezone_selection_keyboard():
    builder = InlineKeyboardBuilder()
    timezone_map = {
        # GMT/WET (UTC+0)
        "🇬🇧 London (GMT)": "Europe/London",
        # CET (UTC+1)
        "🇩🇪 Berlin (CET)": "Europe/Berlin",
        "🇫🇷 Paris (CET)": "Europe/Paris",
        "🇸🇪 Stockholm (CET)": "Europe/Stockholm",
        "🇵🇱 Warsaw (CET)": "Europe/Warsaw",
        "🇨🇿 Prague (CET)": "Europe/Prague",
        # EET (UTC+2)
        "🇪🇪 Tallinn (EET)": "Europe/Tallinn",
        "🇱🇻 Riga (EET)": "Europe/Riga",
        "🇱🇹 Vilnius (EET)": "Europe/Vilnius",
        "🇺🇦 Kiev (EET)": "Europe/Kiev",
        # MSK (UTC+3)
        "🏳️‍🌈 Moscow (MSK)": "Europe/Moscow",
        "🏳️‍🌈 Minsk (MSK)": "Europe/Minsk",
        "🇹🇷 Istanbul (TRT)": "Europe/Istanbul",
        # GET/AMT (UTC+4)
        "🇦🇲 Yerevan (AMT)": "Asia/Yerevan",
        "🇬🇪 Tbilisi (GET)": "Asia/Tbilisi",
        # ALMT (UTC+5)
        "🇰🇿 Almaty (ALMT)": "Asia/Almaty",
        # For Astana, use Asia/Almaty (same timezone as of 2024)
        "🇰🇿 Astana (ALMT)": "Asia/Almaty",
    }

    for name, timezone in timezone_map.items():
        builder.button(text=name, callback_data=f"__tz__{timezone}")

    builder.adjust(1)
    return builder.as_markup()


def create_unsubscribe_keyboard(feeds):
    builder = InlineKeyboardBuilder()
    for feed in feeds.values():
        builder.button(text=feed.channel_name, callback_data=f"__unsub__{feed.channel_id}")

    builder.adjust(1)
    return builder.as_markup()


def create_keywords_feed_keyboard(feeds, channel_filters: dict):
    builder = InlineKeyboardBuilder()
    for feed in feeds.values():
        count = len(channel_filters.get(feed.channel_id, set()))
        label = f"{feed.channel_name}  [{count} keywords]" if count else feed.channel_name
        builder.button(text=label, callback_data=f"__kw__{feed.channel_id}")

    builder.adjust(1)
    return builder.as_markup()


def create_keywords_actions_keyboard(channel_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="Add keywords", callback_data=f"__kw_add__{channel_id}")
    builder.button(text="Clear all", callback_data=f"__kw_clear__{channel_id}")
    builder.button(text="Close", callback_data="__kw_close__")
    builder.adjust(2, 1)
    return builder.as_markup()
