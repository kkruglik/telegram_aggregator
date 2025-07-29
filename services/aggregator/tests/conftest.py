import datetime
import sys
from datetime import time
from pathlib import Path

import pytest  # type: ignore

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from unittest.mock import Mock, patch, AsyncMock

from app.core.user import User  # type: ignore
from app.core.feed import TelegramFeed  # type: ignore
from app.core.enums import Response, ResponseStatus  # type: ignore


@pytest.fixture
def standard_user() -> User:
    return User(
        user_id=12345,
        notification_time=time(12, 0),
        timezone="EET",
        is_premium=False,
    )


@pytest.fixture
def premium_user() -> User:
    return User(
        user_id=12345,
        notification_time=time(12, 0),
        timezone="EET",
        is_premium=True,
    )


@pytest.fixture(params=[
    {"user_id": 12345, "is_premium": False, },
    {"user_id": 67890, "is_premium": True, },
    {"user_id": 11111, "is_premium": False, },
])
def parameterized_user(request):
    """Creates different types of users for comprehensive testing"""
    user_data = request.param
    user = User(
        user_id=user_data["user_id"],
        notification_time=time(12, 0),
        timezone="UTC",
        is_premium=user_data["is_premium"]
    )
    return user


@pytest.fixture
def standard_user_with_feeds() -> User:
    user = User(
        user_id=12345,
        notification_time=time(12, 0),
        timezone="EET",
        is_premium=False,
    )

    for i in range(5):
        user.user_feeds[i] = TelegramFeed(i, f"feed {i}")

    return user


@pytest.fixture
def feed_factory():
    def create_feed(channel_id: int, channel_name: str | None = None):
        mock_feed = Mock(spec=TelegramFeed)
        mock_feed.channel_id = channel_id
        mock_feed.channel_name = channel_name or "test-channel"
        mock_feed.content = {"posts": {1: {
            'updated_at': datetime.datetime(2025, 6, 23, 12, 12, 12),
            'text': 'test-text',
            'channel_id': channel_id,
            'url': 'test-url',
            'id': 1,
        }}}
        return mock_feed

    return create_feed


@pytest.fixture
def mock_database():
    """Mock DatabaseRepository class methods (not instance methods)"""
    with patch('app.core.user.DatabaseRepository') as mock_class:
        mock_class.subscribe_to_feed = AsyncMock(return_value=Response.success())
        mock_class.unsubscribe_from_feed = AsyncMock(return_value=Response.success())  # Simulate successful deletion
        mock_class.update_user = AsyncMock(return_value=Response.success())

        class MockWrapper:
            def __init__(self, class_mock):
                self.class_mock = class_mock
                self.subscribe_to_feed = class_mock.subscribe_to_feed
                self.unsubscribe_from_feed = class_mock.unsubscribe_from_feed
                self.update_user = class_mock.update_user

        yield MockWrapper(mock_class)
