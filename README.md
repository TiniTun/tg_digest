# 📬 Telegram Digest Generator

This project automatically collects messages from Telegram channels, groups them by topics, summarizes them using GPT, and sends a daily digest to a Telegram chat.

It is deployed as a FastAPI application on Google Cloud Run and triggered by Cloud Scheduler.

---

## 🔧 Features

- ✅ Fetch messages from multiple Telegram channels
- ✅ Group by predefined topics (e.g., technology, news)
- ✅ Topic-wise summarization with GPT-4o
- ✅ Caching in Google Cloud Storage
- ✅ Deployment on Cloud Run and triggering via Cloud Scheduler
- ✅ Local debugging and Telegram authorization via Telethon

---

## 🧱 Project Structure
```
telegram_digest/
├── app/
│ ├── main.py # FastAPI app
│ ├── authorize.py # One-time Telegram authorization
│ ├── config.py # Loads environment variables
│ ├── digest_pipeline.py # Main logic
├── .env # local secrets (do not commit)
├── Dockerfile
├── requirements.txt
└── README.md
```
---

## 🚀 Quick Start (Locally)

```bash
git clone https://github.com/YOUR_USERNAME/telegram-digest.git
cd telegram-digest
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 🔑 Telegram Authorization

```bash
python app/authorize.py
```

### ▶️ Run Locally

```bash
uvicorn app.main:app --reload
```

---

## ☁️ Deploy to Cloud Run

```bash
gcloud run deploy telegram-digest \\
  --source . \\
  --region asia-southeast1 \\
  --allow-unauthenticated \\
  --memory=2Gi \\
  --set-secrets \\
    TELEGRAM_BOT_TOKEN=TELEGRAM_BOT_TOKEN:latest,\\
    TELEGRAM_CHAT_ID=TELEGRAM_CHAT_ID:latest,\\
    OPENAI_API_KEY=OPENAI_API_KEY:latest,\\
    API_ID=API_ID:latest,\\
    API_HASH=API_HASH:latest,\\
    GCS_BUCKET_NAME=GCS_BUCKET_NAME:latest
```

---

## 📦 Technologies Used

[FastAPI](https://fastapi.tiangolo.com/)

[Telethon](https://github.com/LonamiWebs/Telethon)

[SentenceTransformers](https://www.sbert.net/)

[OpenAI GPT-4o](https://platform.openai.com/docs/)

[Google Cloud Run](https://cloud.google.com/run)

[Google Cloud Storage](https://cloud.google.com/storage)

[Cloud Scheduler](https://cloud.google.com/scheduler)

---

## 📄 License

MIT — feel free to use and adapt for your own projects.
