import asyncio
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, AsyncMock, MagicMock

from src.app.scraper import TelegramScraperQueue


@pytest.fixture
def telegram_scraper():
    """Create a TelegramScraperQueue instance with a mocked client."""
    with patch("src.app.scraper.TelegramClient") as mock_client_class:
        # Configure the mock client
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # Create the scraper
        scraper = TelegramScraperQueue(
            api_id=12345,
            api_hash="test_hash",
            session_name="test_session"
        )
        
        # Return both the scraper and the mock client for testing
        yield scraper, mock_client


@pytest.mark.asyncio
async def test_start_stop(telegram_scraper):
    """Test starting and stopping the scraper."""
    scraper, mock_client = telegram_scraper
    
    # Test starting
    await scraper.start()
    mock_client.start.assert_called_once()
    assert scraper.running is True
    assert scraper.worker_task is not None
    
    # Test starting when already running
    mock_client.start.reset_mock()
    await scraper.start()
    mock_client.start.assert_not_called()
    
    # Test stopping
    await scraper.stop()
    mock_client.disconnect.assert_called_once()
    assert scraper.running is False
    
    # Test stopping when already stopped
    mock_client.disconnect.reset_mock()
    await scraper.stop()
    mock_client.disconnect.assert_not_called()


@pytest.mark.asyncio
async def test_enqueue_task(telegram_scraper):
    """Test enqueueing a task."""
    scraper, mock_client = telegram_scraper
    
    # Define a test task
    async def test_task(client, arg1, arg2=None):
        return f"Result: {arg1}, {arg2}"
    
    # Enqueue the task
    result = await scraper._enqueue_task(test_task, "test_arg", arg2="test_kwarg")
    
    # Verify the result
    assert result == "Result: test_arg, test_kwarg"
    
    # Verify the client was started
    mock_client.start.assert_called_once()


@pytest.mark.asyncio
async def test_get_today_messages_by_id(telegram_scraper, mock_telegram_message):
    """Test getting today's messages by channel ID."""
    scraper, mock_client = telegram_scraper
    
    # Configure the mock client to return messages
    mock_client.iter_messages = AsyncMock()
    mock_client.iter_messages.return_value = [mock_telegram_message]
    
    # Call the method
    result = await scraper.get_today_messages_by_id(12345)
    
    # Verify the result
    assert result["meta"]["channel_id"] == 12345
    assert len(result["messages"]) == 1
    assert result["messages"][0]["id"] == 1
    assert result["messages"][0]["text"] == "Test message"
    
    # Verify the client method was called correctly
    mock_client.iter_messages.assert_called_once()
    call_args = mock_client.iter_messages.call_args[1]
    assert call_args["entity"] == 12345
    assert call_args["limit"] == 100


@pytest.mark.asyncio
async def test_get_today_messages_by_name(telegram_scraper, mock_telegram_message):
    """Test getting today's messages by channel name."""
    scraper, mock_client = telegram_scraper
    
    # Configure the mock client to return messages
    mock_client.iter_messages = AsyncMock()
    mock_client.iter_messages.return_value = [mock_telegram_message]
    
    # Call the method
    result = await scraper.get_today_messages_by_name("test_channel")
    
    # Verify the result
    assert result["meta"]["channel_id"] == "test_channel"
    assert len(result["messages"]) == 1
    assert result["messages"][0]["id"] == 1
    assert result["messages"][0]["text"] == "Test message"
    
    # Verify the client method was called correctly
    mock_client.iter_messages.assert_called_once()
    call_args = mock_client.iter_messages.call_args[1]
    assert call_args["entity"] == "test_channel"
    assert call_args["limit"] == 100


@pytest.mark.asyncio
async def test_get_channel_id(telegram_scraper, mock_telegram_entity):
    """Test getting a channel ID."""
    scraper, mock_client = telegram_scraper
    
    # Configure the mock client to return an entity
    mock_client.get_entity = AsyncMock()
    mock_client.get_entity.return_value = mock_telegram_entity
    
    # Call the method
    channel_id, username = await scraper.get_channel_id("test_channel")
    
    # Verify the result
    assert channel_id == -10012345  # Should be converted to channel ID format
    assert username == "test_channel"
    
    # Verify the client method was called correctly
    mock_client.get_entity.assert_called_once_with("test_channel")


@pytest.mark.asyncio
async def test_get_today_messages_empty(telegram_scraper):
    """Test getting today's messages when there are none."""
    scraper, mock_client = telegram_scraper
    
    # Configure the mock client to return no messages
    mock_client.iter_messages = AsyncMock()
    mock_client.iter_messages.return_value = []
    
    # Call the method
    result = await scraper.get_today_messages_by_id(12345)
    
    # Verify the result
    assert result["meta"]["channel_id"] == 12345
    assert len(result["messages"]) == 0


@pytest.mark.asyncio
async def test_get_today_messages_old_messages(telegram_scraper):
    """Test getting today's messages when there are only old messages."""
    scraper, mock_client = telegram_scraper
    
    # Create a message from more than 24 hours ago
    old_message = MagicMock()
    old_message.id = 1
    old_message.text = "Old message"
    old_message.date = datetime.now(timezone.utc) - timedelta(hours=25)
    
    # Configure the mock client to return the old message
    mock_client.iter_messages = AsyncMock()
    mock_client.iter_messages.return_value = [old_message]
    
    # Call the method
    result = await scraper.get_today_messages_by_id(12345)
    
    # Verify the result
    assert result["meta"]["channel_id"] == 12345
    assert len(result["messages"]) == 0


@pytest.mark.asyncio
async def test_get_today_messages_empty_text(telegram_scraper):
    """Test getting today's messages when there are messages with empty text."""
    scraper, mock_client = telegram_scraper
    
    # Create a message with empty text
    empty_message = MagicMock()
    empty_message.id = 1
    empty_message.text = ""
    empty_message.date = datetime.now(timezone.utc)
    
    # Configure the mock client to return the empty message
    mock_client.iter_messages = AsyncMock()
    mock_client.iter_messages.return_value = [empty_message]
    
    # Call the method
    result = await scraper.get_today_messages_by_id(12345)
    
    # Verify the result
    assert result["meta"]["channel_id"] == 12345
    assert len(result["messages"]) == 0


@pytest.mark.asyncio
async def test_get_today_messages_exception(telegram_scraper):
    """Test getting today's messages when an exception occurs."""
    scraper, mock_client = telegram_scraper
    
    # Configure the mock client to raise an exception
    mock_client.iter_messages = AsyncMock()
    mock_client.iter_messages.side_effect = Exception("Test exception")
    
    # Call the method and expect an exception
    with pytest.raises(Exception, match="Test exception"):
        await scraper.get_today_messages_by_id(12345)


@pytest.mark.asyncio
async def test_get_channel_id_exception(telegram_scraper):
    """Test getting a channel ID when an exception occurs."""
    scraper, mock_client = telegram_scraper
    
    # Configure the mock client to raise an exception
    mock_client.get_entity = AsyncMock()
    mock_client.get_entity.side_effect = Exception("Test exception")
    
    # Call the method and expect an exception
    with pytest.raises(Exception, match="Test exception"):
        await scraper.get_channel_id("test_channel")


@pytest.mark.asyncio
async def test_process_queue_reconnect(telegram_scraper):
    """Test the queue processor reconnecting when the client is disconnected."""
    scraper, mock_client = telegram_scraper
    
    # Configure the mock client to be disconnected initially, then connected
    mock_client.is_connected.side_effect = [False, True]
    
    # Start the scraper
    await scraper.start()
    
    # Wait a bit for the worker to process
    await asyncio.sleep(0.1)
    
    # Verify the client tried to reconnect
    mock_client.connect.assert_called_once()
    
    # Stop the scraper
    await scraper.stop()


@pytest.mark.asyncio
async def test_process_queue_reconnect_timeout(telegram_scraper):
    """Test the queue processor handling a reconnection timeout."""
    scraper, mock_client = telegram_scraper
    
    # Configure the mock client to be disconnected and timeout on connect
    mock_client.is_connected.return_value = False
    mock_client.connect.side_effect = asyncio.TimeoutError()
    
    # Start the scraper
    await scraper.start()
    
    # Wait a bit for the worker to process
    await asyncio.sleep(0.1)
    
    # Verify the client tried to reconnect
    mock_client.connect.assert_called_once()
    
    # Stop the scraper
    await scraper.stop()


@pytest.mark.asyncio
async def test_process_queue_reconnect_error(telegram_scraper):
    """Test the queue processor handling a reconnection error."""
    scraper, mock_client = telegram_scraper
    
    # Configure the mock client to be disconnected and error on connect
    mock_client.is_connected.return_value = False
    mock_client.connect.side_effect = Exception("Test exception")
    
    # Start the scraper
    await scraper.start()
    
    # Wait a bit for the worker to process
    await asyncio.sleep(0.1)
    
    # Verify the client tried to reconnect
    mock_client.connect.assert_called_once()
    
    # Stop the scraper
    await scraper.stop()