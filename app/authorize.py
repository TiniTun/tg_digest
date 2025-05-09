from telethon.sync import TelegramClient
from .config import API_ID, API_HASH

def authorize():
    client = TelegramClient("digest_session", API_ID, API_HASH)
    client.start()
    print("✅ Авторизация завершена. Сессия сохранена.")

if __name__ == "__main__":
    authorize()