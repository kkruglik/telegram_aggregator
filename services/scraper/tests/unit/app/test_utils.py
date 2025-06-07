import pytest
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

import yaml

from src.app.utils import load_yaml, setup_cloud_logging


def test_load_yaml(tmp_path):
    """Test loading a YAML file."""
    # Create a test YAML file
    test_data = {"test": "value", "nested": {"key": "value"}}
    test_file = tmp_path / "test.yaml"
    with open(test_file, "w") as f:
        yaml.dump(test_data, f)

    # Test loading the file
    result = load_yaml(test_file)
    assert result == test_data

    # Test loading with Path object
    result = load_yaml(Path(test_file))
    assert result == test_data


def test_load_yaml_file_not_found():
    """Test loading a non-existent YAML file."""
    with pytest.raises(FileNotFoundError):
        load_yaml("non_existent_file.yaml")


def test_load_yaml_invalid_yaml(tmp_path):
    """Test loading an invalid YAML file."""
    # Create an invalid YAML file
    test_file = tmp_path / "invalid.yaml"
    with open(test_file, "w") as f:
        f.write("invalid: yaml: content:")

    # Test loading the file
    with pytest.raises(yaml.YAMLError):
        load_yaml(test_file)


@patch("google.cloud.logging.Client")
def test_setup_cloud_logging_success(mock_client):
    """Test successful setup of Google Cloud Logging."""
    # Configure the mock
    mock_client_instance = MagicMock()
    mock_client.return_value = mock_client_instance

    # Call the function
    result = setup_cloud_logging()

    # Verify the result and that the client was called correctly
    assert result is True
    mock_client.assert_called_once()
    mock_client_instance.setup_logging.assert_called_once_with(log_level=logging.INFO)


@patch("google.cloud.logging.Client")
def test_setup_cloud_logging_failure(mock_client):
    """Test failed setup of Google Cloud Logging."""
    # Configure the mock to raise an exception
    mock_client.side_effect = Exception("Test exception")

    # Call the function
    result = setup_cloud_logging()

    # Verify the result
    assert result is False
