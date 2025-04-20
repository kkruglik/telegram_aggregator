import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
env_path = BASE_DIR / '.env'
load_dotenv(dotenv_path=env_path)

BOT_TOKEN = os.getenv('BOT_TOKEN')
API_ID = int(os.getenv('API_ID', 0))
API_HASH = os.getenv('API_HASH', '')
