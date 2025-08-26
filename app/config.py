import os

from dotenv import load_dotenv

load_dotenv("./.env")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Telegram API credentials (optional at import time; validated at use time)
_API_ID_RAW = os.getenv("API_ID")
API_ID = int(_API_ID_RAW) if _API_ID_RAW else None
API_HASH = os.getenv("API_HASH")

GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
GCS_CACHE_PREFIX = "cache"

# Environment
APP_ENV = os.getenv("APP_ENV", "dev")
IS_PROD = APP_ENV.lower() == "prod"

# Topics and channels
TOPICS_AND_CHANNELS = {"Tech": ["@vcnews"]}

TOPICS_CONFIG_URI = "topics.json"
