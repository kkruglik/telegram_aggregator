import logging
import logging.config
import os
from pathlib import Path

import google.cloud.logging  # type: ignore
import yaml  # type: ignore
from aiogram import Bot  # type: ignore
from aiogram.types import BotCommand, BotCommandScopeDefault  # type: ignore

logger = logging.getLogger("news_aggregator")


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


def setup_cloud_logging():
    """Setup Google Cloud Logging."""
    try:
        cloud_logging_client = google.cloud.logging.Client()
        cloud_logging_client.setup_logging(log_level=logging.INFO)

        logger.info("Google Cloud Logging has been configured successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to setup Google Cloud Logging: {e}", exc_info=True)
        return False


async def set_bot_commands(bot: Bot):
    """Set up bot command menu"""
    commands = [
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="subscribe", description="Subscribe to a feed"),
        BotCommand(command="list", description="List subscribed feeds"),
        BotCommand(command="unsubscribe", description="Unsubscribe from a feed"),
        BotCommand(command="notification_time", description="Change notification time"),
        BotCommand(command="timezone", description="Change timezone"),
    ]

    await bot.set_my_commands(commands, BotCommandScopeDefault())
