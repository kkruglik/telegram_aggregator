import logging
import os
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Dict, Optional, Any

from dotenv import load_dotenv
from google.cloud import secretmanager

logger = logging.getLogger('news_aggregator')


@dataclass
class BaseConfig:
    """Base configuration class with common functionality."""

    def __post_init__(self):
        """Load configuration after initialization."""
        self._load_config()

    @cached_property
    def base_dir(self) -> Path:
        """Get the base directory for the application."""
        return Path(__file__).resolve().parents[2]

    def _load_config(self) -> None:
        """Load configuration from environment variables."""
        env_path = self.base_dir / '.env'
        load_dotenv(dotenv_path=env_path)
        self._load_from_env()

    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        for attr_name in self.__annotations__:
            if attr_name.startswith('_') or attr_name == 'base_dir':
                continue

            env_name = attr_name.upper()
            env_value = os.getenv(env_name)

            if env_value is not None:
                setattr(self, attr_name, env_value)

    def as_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary."""
        result = {}
        for attr_name in self.__annotations__:
            if attr_name.startswith('_') or attr_name == 'base_dir':
                continue
            result[attr_name.upper()] = getattr(self, attr_name)
        return result


@dataclass
class PublicConfig(BaseConfig):
    """Configuration class for non-sensitive configuration items."""

    # Default values that can be overridden by environment variables
    db_user: str = field(default="postgres")
    db_host: str = field(default="localhost")
    db_port: str = field(default="5432")
    db_name: str = field(default="news_aggregator")
    scraper_host: str = field(default="scraper")
    scraper_port: str = field(default="8000")

    @cached_property
    def scraper_url(self) -> str:
        """Generate scraper URL from components."""
        return f"http://{self.scraper_host}:{self.scraper_port}"

    def __post_init__(self):
        """Initialize the public configuration."""
        super().__post_init__()
        logger.info("Public configuration loaded")


@dataclass
class SecretConfig(BaseConfig):
    """Configuration class for sensitive configuration items."""

    # Secret configuration values with defaults
    db_password: Optional[str] = field(default=None)
    bot_token: Optional[str] = field(default=None)
    gemini_api_key: Optional[str] = field(default=None)
    gcp_project_id: Optional[str] = field(default=None)

    def __post_init__(self):
        """Initialize the secret configuration."""
        super().__post_init__()

        # After loading from env, try to load missing values from secrets
        if self.gcp_project_id:
            logger.info("GCP_PROJECT_ID is set. Loading missing secrets from Secret Manager")
            self._load_missing_from_secret_manager()

        logger.info("Secret configuration loaded")

    def _get_secret(self, secret_id: str, version_id: str = "latest") -> Optional[str]:
        """Get secret from Google Secret Manager."""
        try:
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{self.gcp_project_id}/secrets/{secret_id}/versions/{version_id}"
            response = client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logger.error(f"Error accessing secret {secret_id}: {e}")
            return None

    def _get_secret_file(self, secret_id: str, file_path: str, version_id: str = "latest") -> bool:
        """Fetch a binary file from Secret Manager and save it to disk."""
        try:
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{self.gcp_project_id}/secrets/{secret_id}/versions/{version_id}"
            response = client.access_secret_version(request={"name": name})

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Write binary data directly to file
            with open(file_path, 'wb') as file:
                file.write(response.payload.data)

            logger.info(f"Secret file saved to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error accessing secret file {secret_id}: {e}")
            return False

    def _load_missing_from_secret_manager(self) -> None:
        """Load missing secrets from Google Secret Manager."""
        secret_attrs = [attr for attr in self.__annotations__
                        if not attr.startswith('_') and attr not in ('base_dir', 'gcp_project_id')]

        for attr_name in secret_attrs:
            current_value = getattr(self, attr_name)

            if current_value is None:
                secret_id = attr_name.upper()
                secret_value = self._get_secret(secret_id)

                if secret_value:
                    setattr(self, attr_name, secret_value)
                    logger.info(f"Loaded {attr_name} from Secret Manager")
                else:
                    logger.info(f"Could not load {attr_name} from Secret Manager")
            else:
                logger.debug(f"Using {attr_name} from environment variables")

        session_path = os.path.join(self.base_dir, 'telegram_scraper.session')
        if self._get_secret_file('telegram_scraper_session', session_path):
            logger.info("Loaded telegram session from Secret Manager")
        else:
            logger.debug("Could not load telegram session from Secret Manager")


@dataclass
class AppConfig:
    """Main application configuration class that combines public and secret configs."""

    public: PublicConfig = field(default_factory=PublicConfig)
    secret: SecretConfig = field(default_factory=SecretConfig)

    @cached_property
    def database_url(self) -> str:
        db_password = self.secret.db_password or ""
        return (f"postgresql://{self.public.db_user}:{db_password}@"
                f"{self.public.db_host}:{self.public.db_port}/{self.public.db_name}")

    def as_dict(self) -> Dict[str, Any]:
        """Return all configuration as a flat dictionary."""
        result = {}
        result.update(self.public.as_dict())
        result.update(self.secret.as_dict())
        result['DATABASE_URL'] = self.database_url
        result['SCRAPER_URL'] = self.public.scraper_url
        return result


config = AppConfig()

BOT_TOKEN = config.secret.bot_token
DB_USER = config.public.db_user
DB_PASSWORD = config.secret.db_password
DB_HOST = config.public.db_host
DB_PORT = config.public.db_port
DB_NAME = config.public.db_name
DATABASE_URL = config.database_url
GEMINI_API_KEY = config.secret.gemini_api_key
SCRAPER_URL = config.public.scraper_url
GCP_PROJECT_ID = config.secret.gcp_project_id
