import os
import pytest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import yaml
from fastapi.testclient import TestClient

from src.app.config import AppConfig, ScraperConfig, GCPConfig
from src.app.models import Message, ChannelMeta, ChannelMessages


@pytest.fixture
def test_config_path():
    """Path to test configuration file."""
    return Path("tests/fixtures/config-test.yaml")


@pytest.fixture
def test_config_data():
    """Test configuration data."""
    return {
        "scraper": {
            "session_name": "test_session",
            "api_id": 12345,
            "api_hash": "test_hash"
        },
        "gcp": {
            "project_id": "test-project"
        }
    }


@pytest.fixture
def test_config_file(test_config_path, test_config_data):
    """Create a test configuration file."""
    os.makedirs(test_config_path.parent, exist_ok=True)
    with open(test_config_path, "w") as f:
        yaml.dump(test_config_data, f)
    yield test_config_path
    # Clean up
    if test_config_path.exists():
        os.remove(test_config_path)


@pytest.fixture
def app_config():
    """Create a test AppConfig instance."""
    config = AppConfig()
    config.scraper = ScraperConfig(
        session_name="test_session",
        api_id=12345,
        api_hash="test_hash"
    )
    config.gcp = GCPConfig(project_id="test-project")
    return config


@pytest.fixture
def mock_telegram_client():
    """Mock TelegramClient for testing."""
    client = AsyncMock()
    client.start.return_value = None
    client.disconnect.return_value = None
    client.is_connected.return_value = True
    return client


@pytest.fixture
def mock_telegram_message():
    """Mock Telegram message for testing."""
    message = MagicMock()
    message.id = 1
    message.text = "Test message"
    message.date = datetime.now(timezone.utc)
    return message


@pytest.fixture
def mock_telegram_entity():
    """Mock Telegram entity for testing."""
    entity = MagicMock()
    entity.id = 12345
    entity.username = "test_channel"
    entity.megagroup = True
    return entity


@pytest.fixture
def sample_channel_messages():
    """Sample ChannelMessages for testing."""
    return ChannelMessages(
        meta=ChannelMeta(
            channel_id="12345",
            date=datetime.now(timezone.utc)
        ),
        messages=[
            Message(id=1, text="Test message 1"),
            Message(id=2, text="Test message 2")
        ]
    )


@pytest.fixture
def api_client():
    """Test client for the FastAPI application."""
    # We need to patch the environment and config before importing the app
    with patch.dict(os.environ, {"CONFIG_NAME": "config-test.yaml"}):
        with patch("src.app.main.initialize_config") as mock_init_config:
            mock_init_config.return_value = AppConfig()
            mock_init_config.return_value.scraper = ScraperConfig(
                session_name="test_session",
                api_id=12345,
                api_hash="test_hash"
            )
            mock_init_config.return_value.gcp = GCPConfig(project_id="")

            # Now we can import the app
            from src.app.main import app

            # Patch the TelegramScraperQueue
            with patch("src.app.main.TelegramScraperQueue") as mock_queue_class:
                mock_queue = AsyncMock()
                mock_queue_class.return_value = mock_queue

                # Configure the mock queue methods
                mock_queue.start.return_value = None
                mock_queue.get_today_messages_by_id.return_value = {
                    "meta": {
                        "channel_id": 12345,
                        "date": datetime.now(timezone.utc)
                    },
                    "messages": [
                        {"id": 1, "text": "Test message 1"},
                        {"id": 2, "text": "Test message 2"}
                    ]
                }
                mock_queue.get_today_messages_by_name.return_value = {
                    "meta": {
                        "channel_id": "test_channel",
                        "date": datetime.now(timezone.utc)
                    },
                    "messages": [
                        {"id": 1, "text": "Test message 1"},
                        {"id": 2, "text": "Test message 2"}
                    ]
                }
                mock_queue.get_channel_id.return_value = (12345, "test_channel")

                # Create and return the test client
                client = TestClient(app)
                yield client
