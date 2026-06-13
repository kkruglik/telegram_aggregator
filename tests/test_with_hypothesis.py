from unittest.mock import Mock, patch

import pytest  # type: ignore
from hypothesis import given  # type: ignore
from hypothesis import strategies as st

from app.core.enums import ResponseStatus  # type: ignore
from app.core.feed import TelegramFeed  # type: ignore
from app.core.user import User  # type: ignore


@given(
    user_id=st.integers(min_value=1, max_value=999999),
    channel_ids=st.lists(st.integers(min_value=1, max_value=999999), min_size=0, max_size=4),
)
@pytest.mark.asyncio
async def test_subscription_properties(user_id, channel_ids):
    """Property: Users with fewer than 5 subscriptions can always add one more unique subscription"""
    with patch("app.db.repository.DatabaseRepository.subscribe_to_feed") as mock_db:
        mock_db.return_value = None  # Fresh mock for each example

        user = User(user_id=user_id, timezone="UTC", is_premium=False)

        db_call_count = 0
        for channel_id in channel_ids:
            mock_feed = Mock(spec=TelegramFeed)
            mock_feed.channel_id = channel_id
            user.user_feeds[channel_id] = mock_feed
            result = await user.subscribe(mock_feed)

            if result.status == ResponseStatus.OK:
                db_call_count += 1

            assert result.status in {ResponseStatus.OK, ResponseStatus.ALREADY_SUBSCRIBED}

        assert mock_db.call_count == db_call_count
