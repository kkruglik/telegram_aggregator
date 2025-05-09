import logging
import os
from dataclasses import dataclass, field, fields
from functools import cached_property
from pathlib import Path
from typing import Dict, Optional, Any

import yaml
from google.cloud import secretmanager

logger = logging.getLogger("news_aggregator")


@dataclass
class ConfigSection:
    """Base class for configuration sections."""

    def __post_init__(self):
        """Post-initialization processing."""
        pass


@dataclass
class DatabaseConfig(ConfigSection):
    """Database configuration section."""

    user: str
    host: str
    port: str
    name: str
    password: Optional[str] = None

    @cached_property
    def url(self) -> str:
        """Generate database URL from components."""
        password = self.password or ""
        return f"postgresql://{self.user}:{password}@{self.host}:{self.port}/{self.name}"


@dataclass
class ScraperConfig(ConfigSection):
    """Scraper configuration section."""

    host: str
    port: str

    @cached_property
    def url(self) -> str:
        """Generate scraper URL from components."""
        return f"http://{self.host}:{self.port}"


@dataclass
class GCPConfig(ConfigSection):
    """Google Cloud Platform configuration section."""

    project_id: str


@dataclass
class BotConfig(ConfigSection):
    """Bot configuration section."""

    token: Optional[str] = None


@dataclass
class GeminiConfig(ConfigSection):
    """Gemini configuration section."""

    token: Optional[str] = None


@dataclass
class AppConfig:
    """Main application configuration class that combines all config sections."""

    # Base directory for the application
    _base_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parents[2])

    # Configuration sections
    database: Optional[DatabaseConfig] = None
    scraper: Optional[ScraperConfig] = None
    gcp: Optional[GCPConfig] = None
    bot: Optional[BotConfig] = None
    gemini: Optional[GeminiConfig] = None

    def load_from_yaml(self, yaml_path: Path) -> None:
        """Load configuration from YAML file."""
        logger.info(f"Loading configuration from {yaml_path}")

        if not yaml_path.exists():
            raise FileNotFoundError(f"Configuration file {yaml_path} does not exist")

        try:
            with open(yaml_path, "r") as file:
                config_data = yaml.safe_load(file)

            if not config_data:
                raise ValueError("Configuration file is empty")

            # Create configuration sections from YAML
            self._create_from_dict(config_data)

            logger.info("Configuration loaded from YAML file")
        except Exception as e:
            logger.error(f"Error loading configuration from YAML: {e}")
            raise

    def load_from_secret_manager(self) -> None:
        """Load missing values from Google Secret Manager."""
        if not self.gcp or not self.gcp.project_id:
            logger.info("GCP project ID not set, skipping Secret Manager")
            return

        logger.info(f"Loading missing values from Secret Manager for project {self.gcp.project_id}")

        # Check all sections
        section_names = ["database", "scraper", "bot", "gemini"]
        for section_name in section_names:
            if not hasattr(self, section_name) or getattr(self, section_name) is None:
                continue

            section = getattr(self, section_name)

            # Get all fields for this section
            for field_obj in fields(section):
                field_name = field_obj.name
                current_value = getattr(section, field_name)

                # Only load from Secret Manager if value is None
                if current_value is None:
                    # Generate Secret Manager secret ID
                    # Format: SECTION_FIELD (e.g., DATABASE_PASSWORD)
                    secret_id = f"{section_name.upper()}_{field_name.upper()}"

                    secret_value = self._get_secret(secret_id)

                    if secret_value:
                        setattr(section, field_name, secret_value)
                        logger.info(f"Loaded {section_name}.{field_name} from Secret Manager")
                    else:
                        # Log a warning but continue - some values are optional
                        logger.warning(
                            f"Could not load {section_name}.{field_name} from Secret Manager"
                        )

    def _create_from_dict(self, config_dict: Dict[str, Dict[str, Any]]) -> None:
        """Create configuration sections from dictionary."""
        if "database" in config_dict:
            self.database = DatabaseConfig(**config_dict["database"])

        if "scraper" in config_dict:
            self.scraper = ScraperConfig(**config_dict["scraper"])

        if "gcp" in config_dict:
            self.gcp = GCPConfig(**config_dict["gcp"])

        if "bot" in config_dict:
            self.bot = BotConfig(**config_dict["bot"])

        if "gemini" in config_dict:
            self.gemini = GeminiConfig(**config_dict["gemini"])

    def _get_secret(self, secret_id: str, version_id: str = "latest") -> Optional[str]:
        """Get secret from Google Secret Manager."""
        try:
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{self.gcp.project_id}/secrets/{secret_id}/versions/{version_id}"
            response = client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logger.error(f"Error accessing secret {secret_id}: {e}")
            return None

    def _get_secret_file(self, secret_id: str, file_path: str, version_id: str = "latest") -> bool:
        """Fetch a binary file from Secret Manager and save it to disk."""
        try:
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{self.gcp.project_id}/secrets/{secret_id}/versions/{version_id}"
            response = client.access_secret_version(request={"name": name})

            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, "wb") as file:
                file.write(response.payload.data)

            logger.info(f"Secret file saved to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error accessing secret file {secret_id}: {e}")
            return False


def initialize_config(yaml_path: Path) -> AppConfig:
    """Initialize configuration from YAML and Secret Manager."""
    app_config = AppConfig()
    app_config.load_from_yaml(yaml_path)
    app_config.load_from_secret_manager()
    logger.info("Configuration initialization complete")
    return app_config


default_config_path = (
    Path(__file__).resolve().parents[2] / "config" / "aggregator" / "config-local.yaml"
)

config = initialize_config(default_config_path)

BOT_TOKEN = config.bot.token if config.bot else None
DATABASE_URL = config.database.url if config.database else None
DB_USER = config.database.user if config.database else None
DB_PASSWORD = config.database.password if config.database else None
DB_HOST = config.database.host if config.database else None
DB_PORT = config.database.port if config.database else None
DB_NAME = config.database.name if config.database else None
GEMINI_API_KEY = config.gemini.token if config.gemini else None
SCRAPER_URL = config.scraper.url if config.scraper else None
