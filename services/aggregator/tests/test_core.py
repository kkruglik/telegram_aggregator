from unittest.mock import call

import pytest  # type: ignore

from app.core.enums import ResponseStatus  # type: ignore


@pytest.mark.asyncio
async def test_standard_user_subscribe_success(standard_user, mock_database, feed_factory):
    """Test successful subscription with correct expectations"""
    user_id = standard_user.id
    feed = feed_factory(channel_id=98765)

    assert len(standard_user.user_feeds) == 0

    result = await standard_user.subscribe(feed)

    assert result.status == ResponseStatus.OK
    assert feed.channel_id in standard_user.user_feeds
    assert mock_database.subscribe_to_feed.call_count == 1
    mock_database.subscribe_to_feed.assert_called_once_with(user_id, feed.channel_id)


@pytest.mark.asyncio
async def test_standard_user_subscribe_five_channels_success(
    standard_user, mock_database, feed_factory
):
    user_id = standard_user.id
    expected_calls = []

    for channel_id in range(1, 6):
        mock_feed = feed_factory(channel_id=channel_id)
        result = await standard_user.subscribe(mock_feed)
        expected_calls.append(call(user_id, channel_id))
        assert result.status == ResponseStatus.OK
        assert mock_feed.channel_id in standard_user.user_feeds

    assert mock_database.subscribe_to_feed.call_count == 5
    mock_database.subscribe_to_feed.assert_has_calls(expected_calls)


@pytest.mark.asyncio
async def test_standard_user_subscribe_limit_reached(standard_user, mock_database, feed_factory):
    user_id = standard_user.id
    expected_calls = []

    for channel_id in range(5):
        mock_feed = feed_factory(channel_id=channel_id)
        result = await standard_user.subscribe(mock_feed)

        assert result.status == ResponseStatus.OK
        assert mock_feed.channel_id in standard_user.user_feeds
        expected_calls.append(call(user_id, channel_id))

    mock_feed = feed_factory(channel_id=99)
    result = await standard_user.subscribe(mock_feed)

    assert result.status == ResponseStatus.LIMIT_REACHED
    assert mock_feed.channel_id not in standard_user.user_feeds

    assert mock_database.subscribe_to_feed.call_count == 5
    mock_database.subscribe_to_feed.assert_has_calls(expected_calls)


@pytest.mark.asyncio
async def test_premium_user_subscribe_success(premium_user, mock_database, feed_factory):
    user_id = premium_user.id
    expected_calls = []

    for channel_id in range(6):
        mock_feed = feed_factory(channel_id=channel_id)
        result = await premium_user.subscribe(mock_feed)

        assert result.status == ResponseStatus.OK
        assert mock_feed.channel_id in premium_user.user_feeds
        expected_calls.append(call(user_id, channel_id))

    assert mock_database.subscribe_to_feed.call_count == 6
    mock_database.subscribe_to_feed.assert_has_calls(expected_calls)


@pytest.mark.asyncio
async def test_standard_user_unsubscribe_success(standard_user, mock_database, feed_factory):
    """Test unsubscribing from an existing feed"""
    channel_id = 1
    feed = feed_factory(channel_id=channel_id)

    subscribe_result = await standard_user.subscribe(feed)
    assert subscribe_result.status == ResponseStatus.OK

    result = await standard_user.unsubscribe(channel_id)

    assert result.status == ResponseStatus.OK
    assert channel_id not in standard_user.user_feeds
    assert mock_database.unsubscribe_from_feed.call_count == 1
    mock_database.unsubscribe_from_feed.assert_called_once_with(standard_user.id, channel_id)


@pytest.mark.parametrize(
    "channel_id,expected_status",
    [
        (123, ResponseStatus.OK),
        (456, ResponseStatus.OK),
        (999999, ResponseStatus.OK),
    ],
)
@pytest.mark.asyncio
async def test_subscribe_different_channels(
    standard_user, mock_database, feed_factory, channel_id, expected_status
):
    """Test subscription to different channel IDs"""
    feed = feed_factory(channel_id=channel_id)

    result = await standard_user.subscribe(feed)

    assert result.status == expected_status
    assert channel_id in standard_user.user_feeds
    mock_database.subscribe_to_feed.assert_called_once_with(standard_user.id, channel_id)


@pytest.mark.asyncio
async def test_unsubscribe_all_feeds(standard_user, mock_database, feed_factory):
    """Test unsubscribing from all feeds one by one"""

    for i in range(5):
        feed = feed_factory(channel_id=i)
        result = await standard_user.subscribe(feed)
        assert result.status == ResponseStatus.OK

    assert len(standard_user.user_feeds) == 5

    for i in range(5):
        result = await standard_user.unsubscribe(channel_id=i)
        assert result.status == ResponseStatus.OK

    assert len(standard_user.user_feeds) == 0

    assert mock_database.subscribe_to_feed.call_count == 5
    assert mock_database.unsubscribe_from_feed.call_count == 5


@pytest.mark.asyncio
async def test_upgrade_user_to_premium(standard_user, mock_database, feed_factory):
    """Test upgrading user to premium status"""
    for i in range(5):
        feed = feed_factory(channel_id=i)
        result = await standard_user.subscribe(feed)
        assert result.status == ResponseStatus.OK

    assert len(standard_user.user_feeds) == 5
    assert mock_database.subscribe_to_feed.call_count == 5
    assert not standard_user.is_premium

    new_feed = feed_factory(channel_id=6)
    result = await standard_user.subscribe(new_feed)
    assert result.status == ResponseStatus.LIMIT_REACHED
    assert len(standard_user.user_feeds) == 5

    await standard_user.upgrade_user_to_premium()
    assert mock_database.update_user.call_count == 1
    assert standard_user.is_premium
    mock_database.update_user.assert_called_once_with(standard_user.id, is_premium=True)

    result = await standard_user.subscribe(new_feed)
    assert result.status == ResponseStatus.OK
    assert mock_database.subscribe_to_feed.call_count == 6
    assert len(standard_user.user_feeds) == 6
