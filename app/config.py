import os

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]

GCS_BUCKET_NAME = os.environ["GCS_BUCKET_NAME"]
GCS_CACHE_PREFIX = "cache"

# Topics and channels
TOPICS_AND_CHANNELS = {
    'Tech': ['@vcnews', '@whackdoor', '@Wylsared'],
    'News': ['@meduzalive', '@bankrollo', '@lentachtrue'],
    'Productivity': ['@donetsraw']
}
