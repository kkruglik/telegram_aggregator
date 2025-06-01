import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.app.config import AppConfig, ScraperConfig, GCPConfig, initialize_config


def test_config_section_post_init():
    """Test the ConfigSection.__post_init__ method."""
    # This is a no-op method, but we should test it for coverage
    config = ScraperConfig(session_name="test")
    # No assertion needed, just checking it doesn't raise an exception


def test_scraper_config():
    """Test the ScraperConfig class."""
    config = ScraperConfig(
        session_name="test_session",
        api_id=12345,
        api_hash="test_hash"
    )
    assert config.session_name == "test_session"
    assert config.api_id == 12345
    assert config.api_hash == "test_hash"

    # Test with optional fields omitted
    config = ScraperConfig(session_name="test_session")
    assert config.session_name == "test_session"
    assert config.api_id is None
    assert config.api_hash is None


def test_gcp_config():
    """Test the GCPConfig class."""
    config = GCPConfig(project_id="test-project")
    assert config.project_id == "test-project"


def test_app_config_init():
    """Test the AppConfig initialization."""
    config = AppConfig()
    assert config.scraper is None
    assert config.gcp is None
    assert isinstance(config._base_dir, Path)


def test_app_config_load_from_yaml(test_config_file):
    """Test loading configuration from a YAML file."""
    config = AppConfig()
    config.load_from_yaml(test_config_file)
    
    assert isinstance(config.scraper, ScraperConfig)
    assert config.scraper.session_name == "test_session"
    assert config.scraper.api_id == 12345
    assert config.scraper.api_hash == "test_hash"
    
    assert isinstance(config.gcp, GCPConfig)
    assert config.gcp.project_id == "test-project"


def test_app_config_load_from_yaml_file_not_found():
    """Test loading configuration from a non-existent YAML file."""
    config = AppConfig()
    with pytest.raises(FileNotFoundError):
        config.load_from_yaml(Path("non_existent_file.yaml"))


def test_app_config_load_from_yaml_empty_file(tmp_path):
    """Test loading configuration from an empty YAML file."""
    # Create an empty YAML file
    empty_file = tmp_path / "empty.yaml"
    with open(empty_file, "w") as f:
        f.write("")
    
    config = AppConfig()
    with pytest.raises(ValueError, match="Configuration file is empty"):
        config.load_from_yaml(empty_file)


@patch("src.app.config.AppConfig.load_from_yaml")
@patch("src.app.config.AppConfig.load_from_secret_manager")
def test_initialize_config(mock_load_from_secret_manager, mock_load_from_yaml):
    """Test the initialize_config function."""
    # Configure the mocks
    mock_load_from_yaml.return_value = None
    mock_load_from_secret_manager.return_value = None
    
    # Call the function
    config = initialize_config(Path("test_config.yaml"))
    
    # Verify the mocks were called
    mock_load_from_yaml.assert_called_once_with(Path("test_config.yaml"))
    mock_load_from_secret_manager.assert_called_once()
    
    # Verify the return value
    assert isinstance(config, AppConfig)


@patch("src.app.config.secretmanager.SecretManagerServiceClient")
def test_app_config_load_from_secret_manager_no_gcp(mock_client):
    """Test loading from Secret Manager when GCP config is not set."""
    config = AppConfig()
    config.gcp = None
    
    # Call the function
    config.load_from_secret_manager()
    
    # Verify the client was not called
    mock_client.assert_not_called()


@patch("src.app.config.secretmanager.SecretManagerServiceClient")
def test_app_config_load_from_secret_manager_with_gcp(mock_client):
    """Test loading from Secret Manager when GCP config is set."""
    # Configure the mock
    mock_client_instance = MagicMock()
    mock_client.return_value = mock_client_instance
    
    # Configure the mock response
    mock_response = MagicMock()
    mock_response.payload.data.decode.return_value = "test_value"
    mock_client_instance.access_secret_version.return_value = mock_response
    
    # Create a config with GCP and scraper sections
    config = AppConfig()
    config.gcp = GCPConfig(project_id="test-project")
    config.scraper = ScraperConfig(session_name="test_session", api_id=None, api_hash=None)
    
    # Call the function
    config.load_from_secret_manager()
    
    # Verify the client was called for each missing value
    assert mock_client_instance.access_secret_version.call_count == 2