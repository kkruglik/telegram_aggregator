import pytest
from datetime import datetime, timezone
from src.app.models import (
    Message,
    ChannelMeta,
    ChannelMessages,
    ChannelRequestByID,
    ChannelRequestByName,
    ChannelIDRequest,
    ChannelIDResponse,
)


def test_message_model():
    """Test the Message model."""
    message = Message(id=1, text="Test message")
    assert message.id == 1
    assert message.text == "Test message"


def test_channel_meta_model():
    """Test the ChannelMeta model."""
    now = datetime.now(timezone.utc)
    meta = ChannelMeta(channel_id="12345", date=now)
    assert meta.channel_id == "12345"
    assert meta.date == now


def test_channel_messages_model():
    """Test the ChannelMessages model."""
    now = datetime.now(timezone.utc)
    meta = ChannelMeta(channel_id="12345", date=now)
    messages = [
        Message(id=1, text="Test message 1"),
        Message(id=2, text="Test message 2"),
    ]
    channel_messages = ChannelMessages(meta=meta, messages=messages)
    assert channel_messages.meta == meta
    assert len(channel_messages.messages) == 2
    assert channel_messages.messages[0].id == 1
    assert channel_messages.messages[1].text == "Test message 2"


def test_channel_request_by_id_model():
    """Test the ChannelRequestByID model."""
    request = ChannelRequestByID(channel_id=12345)
    assert request.channel_id == 12345


def test_channel_request_by_name_model():
    """Test the ChannelRequestByName model."""
    request = ChannelRequestByName(channel_name="test_channel")
    assert request.channel_name == "test_channel"


def test_channel_id_request_model():
    """Test the ChannelIDRequest model."""
    request = ChannelIDRequest(channel="test_channel")
    assert request.channel == "test_channel"


def test_channel_id_response_model():
    """Test the ChannelIDResponse model."""
    response = ChannelIDResponse(channel_id=12345, username="test_channel")
    assert response.channel_id == 12345
    assert response.username == "test_channel"

    # Test optional username
    response = ChannelIDResponse(channel_id=12345)
    assert response.channel_id == 12345
    assert response.username is None