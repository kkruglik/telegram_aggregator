import pytest
from fastapi import HTTPException
from unittest.mock import patch, AsyncMock

from src.app.models import (
    ChannelRequestByID,
    ChannelRequestByName,
    ChannelIDRequest,
)


def test_health_check(api_client):
    """Test the health check endpoint."""
    response = api_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "telegram-scraper"}


def test_get_messages_by_id(api_client):
    """Test getting messages by channel ID."""
    response = api_client.post("/messages_by_id", json={"channel_id": 12345})
    assert response.status_code == 200
    data = response.json()
    assert "meta" in data
    assert "messages" in data
    assert data["meta"]["channel_id"] == 12345
    assert len(data["messages"]) == 2
    assert data["messages"][0]["id"] == 1
    assert data["messages"][0]["text"] == "Test message 1"


def test_get_messages_by_name(api_client):
    """Test getting messages by channel name."""
    response = api_client.post("/messages_by_name", json={"channel_name": "test_channel"})
    assert response.status_code == 200
    data = response.json()
    assert "meta" in data
    assert "messages" in data
    assert data["meta"]["channel_id"] == "test_channel"
    assert len(data["messages"]) == 2
    assert data["messages"][0]["id"] == 1
    assert data["messages"][0]["text"] == "Test message 1"


def test_get_channel_id(api_client):
    """Test getting a channel ID."""
    response = api_client.post("/channel_id", json={"channel": "test_channel"})
    assert response.status_code == 200
    data = response.json()
    assert data["channel_id"] == 12345
    assert data["username"] == "test_channel"


@patch("src.app.main.telegram_queue")
def test_get_messages_by_id_error(mock_queue, api_client):
    """Test error handling when getting messages by ID."""
    # Configure the mock to raise an exception
    mock_queue.get_today_messages_by_id.side_effect = Exception("Test exception")
    
    # Make the request
    response = api_client.post("/messages_by_id", json={"channel_id": 12345})
    
    # Verify the response
    assert response.status_code == 500
    assert "Failed to get messages" in response.json()["detail"]


@patch("src.app.main.telegram_queue")
def test_get_messages_by_name_error(mock_queue, api_client):
    """Test error handling when getting messages by name."""
    # Configure the mock to raise an exception
    mock_queue.get_today_messages_by_name.side_effect = Exception("Test exception")
    
    # Make the request
    response = api_client.post("/messages_by_name", json={"channel_name": "test_channel"})
    
    # Verify the response
    assert response.status_code == 500
    assert "Failed to get messages" in response.json()["detail"]


@patch("src.app.main.telegram_queue")
def test_get_channel_id_error(mock_queue, api_client):
    """Test error handling when getting a channel ID."""
    # Configure the mock to raise an exception
    mock_queue.get_channel_id.side_effect = Exception("Test exception")
    
    # Make the request
    response = api_client.post("/channel_id", json={"channel": "test_channel"})
    
    # Verify the response
    assert response.status_code == 500
    assert "Failed to get channel ID" in response.json()["detail"]