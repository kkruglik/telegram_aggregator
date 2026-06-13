from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, create_autospec, patch

import pytest

with patch("telethon.TelegramClient", MagicMock), patch("openai.AsyncOpenAI", MagicMock):
    from telethon.types import Channel

    from app.services.scraper import TelegramScraperQueue


async def _async_iter(items):
    for item in items:
        yield item


def _make_message(text: str, age_hours: float) -> MagicMock:
    msg = MagicMock()
    msg.text = text
    msg.id = id(msg)
    msg.date = datetime.now(tz=UTC) - timedelta(hours=age_hours)
    return msg


# ---------------------------------------------------------------------------
# _get_today_messages
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_recent_message_included():
    client = MagicMock()
    client.iter_messages.return_value = _async_iter([_make_message("breaking news", age_hours=1)])

    result = await TelegramScraperQueue._get_today_messages(client, channel_name="test")

    assert len(result["messages"]) == 1
    assert result["messages"][0]["text"] == "breaking news"


@pytest.mark.asyncio
async def test_old_message_excluded():
    client = MagicMock()
    client.iter_messages.return_value = _async_iter([_make_message("old news", age_hours=25)])

    result = await TelegramScraperQueue._get_today_messages(client, channel_name="test")

    assert result["messages"] == []


@pytest.mark.asyncio
async def test_empty_text_skipped():
    client = MagicMock()
    client.iter_messages.return_value = _async_iter([
        _make_message("", age_hours=1),
        _make_message(None, age_hours=1),
    ])

    result = await TelegramScraperQueue._get_today_messages(client, channel_name="test")

    assert result["messages"] == []


@pytest.mark.asyncio
async def test_only_recent_non_empty_returned():
    client = MagicMock()
    client.iter_messages.return_value = _async_iter([
        _make_message("good", age_hours=2),
        _make_message("", age_hours=1),
        _make_message("old", age_hours=25),
    ])

    result = await TelegramScraperQueue._get_today_messages(client, channel_name="test")

    assert len(result["messages"]) == 1
    assert result["messages"][0]["text"] == "good"


# ---------------------------------------------------------------------------
# _get_channel_id
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_channel_id_gets_negative_100_prefix():
    client = MagicMock()
    entity = create_autospec(Channel, instance=True)
    entity.id = 1027423644
    entity.username = "kolezev"
    entity.megagroup = True
    client.get_entity = AsyncMock(return_value=entity)

    channel_id, username = await TelegramScraperQueue._get_channel_id(client, "@kolezev")

    assert channel_id == -1001027423644
    assert username == "kolezev"


@pytest.mark.asyncio
async def test_channel_id_raises_on_error():
    client = MagicMock()
    client.get_entity = AsyncMock(side_effect=ValueError("not found"))

    with pytest.raises(ValueError, match="not found"):
        await TelegramScraperQueue._get_channel_id(client, "@nonexistent")
