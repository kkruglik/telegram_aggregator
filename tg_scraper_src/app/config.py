import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import secretmanager

logger = logging.getLogger(__name__)

API_ID = None
API_HASH = None
GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID')


def get_secret(project_id, secret_id, version_id="latest"):
    """
    Accesses a secret version from Google Secret Manager.
    """
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"Error accessing secret {secret_id}: {e}")
        return None


def get_secret_file(project_id, secret_id, file_path, version_id="latest"):
    """
    Fetches a binary file from Secret Manager and saves it to disk.
    """
    try:
        from google.cloud import secretmanager
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
        response = client.access_secret_version(request={"name": name})

        # Write binary data directly to file
        with open(file_path, 'wb') as file:
            file.write(response.payload.data)

        logger.info(f"Secret file saved to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error accessing secret file {secret_id}: {e}")
        return False


def load_config():
    """Load configuration and set module-level variables"""
    global API_ID, API_HASH, GCP_PROJECT_ID

    # Load from environment variables first
    BASE_DIR = Path(__file__).resolve().parents[2]
    env_path = BASE_DIR / '.env'
    load_dotenv(dotenv_path=env_path)

    if GCP_PROJECT_ID:
        logger.info(f"GCP_PROJECT_ID is set. Attempting to load secrets from Secret Manager")

        # List of secrets to fetch from Secret Manager
        secret_mapping = {
            'API_HASH': 'API_HASH',
            'API_ID': 'API_ID',
        }

        # Fetch each secret
        for secret_id, var_name in secret_mapping.items():
            secret_value = get_secret(GCP_PROJECT_ID, secret_id)
            if secret_value:
                globals()[var_name] = secret_value
                logger.info(f"Loaded {var_name} from Secret Manager")
            else:
                logger.info(f"Using {var_name} from environment variables")

        # Also fetch and save the session file
        session_path = os.path.join(BASE_DIR, 'telegram_scraper.session')
        if get_secret_file(GCP_PROJECT_ID, 'telegram_scraper_session', session_path):
            logger.info("Loaded telegram session from Secret Manager")
        else:
            logger.warning("Could not load telegram session from Secret Manager")

    logger.info("Configuration loaded successfully")

    # Return a config dictionary for optional use
    return {
        'API_ID': API_ID,
        'API_HASH': API_HASH
    }


load_config()

