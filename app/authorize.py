from telethon.sync import TelegramClient

from .config import API_HASH, API_ID


def authorize():
    if not API_ID or not API_HASH:
        msg = (
            "Missing API_ID/API_HASH. Set env vars or .env and run: "
            "python -m dotenv run -- python -m app.authorize"
        )
        raise RuntimeError(msg)
    client = TelegramClient("digest_session", API_ID, API_HASH)
    client.start()
    print("✅ Authorization is completed. The session is saved.")


if __name__ == "__main__":
    authorize()
