import os
import logging
import logging.config
from pathlib import Path
from timezonefinder import TimezoneFinder


import yaml


def load_yaml(path: str | Path) -> dict:
    with open(path, "rt") as f:
        try:
            config = yaml.safe_load(f.read())
            return config
        except yaml.YAMLError as exc:
            raise exc


def setup_logging(
    default_path="logging_config.yaml", default_level=logging.INFO, env_key="LOG_CONFIG"
):
    """Setup logging configuration from YAML file

    Args:
        default_path (str): Path to the logging config file
        default_level (int): Default logging level if config file not found
        env_key (str): Environment variable that can override the config path
    """
    path = os.getenv(env_key, default_path)

    if os.path.exists(path):
        with open(path, "rt") as f:
            try:
                config = yaml.safe_load(f.read())

                # Ensure logs directory exists
                log_dir = os.path.dirname(config["handlers"]["file"]["filename"])
                if not os.path.exists(log_dir):
                    os.makedirs(log_dir)

                logging.config.dictConfig(config)
                logging.info(f"Logging configured using file: {path}")
            except Exception as e:
                print(f"Error loading logging configuration from {path}: {e}")
                print("Using default logging configuration")
                logging.basicConfig(level=default_level)
    else:
        print(f"Logging config file not found at {path}")
        print("Using default logging configuration")
        logging.basicConfig(level=default_level)


def get_timezone_string(latitude: float, longitude: float):
    """Get IANA timezone identifier from coordinates"""
    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lng=longitude, lat=latitude)
    return timezone_str
