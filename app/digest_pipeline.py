import os
import json
import requests
from datetime import datetime, timedelta
from collections import defaultdict

from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN
from openai import OpenAI

from google.cloud import storage

from .config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, OPENAI_API_KEY, API_ID, API_HASH, TOPICS_AND_CHANNELS, GCS_BUCKET_NAME, GCS_CACHE_PREFIX

CACHE_TIME = 2  # hours

storage_client = storage.Client()


client = OpenAI(api_key=OPENAI_API_KEY)

def load_cache_from_gcs(date_str):
    path = f"{GCS_CACHE_PREFIX}/{date_str}.json"
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob(path)

    if blob.exists():
        data = blob.download_as_text()
        return json.loads(data)
    else:
        return None

def save_cache_to_gcs(date_str, messages_by_topic):
    path = f"{GCS_CACHE_PREFIX}/{date_str}.json"
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob(path)

    blob.upload_from_string(
        json.dumps(messages_by_topic, ensure_ascii=False, indent=2),
        content_type="application/json"
    )

#def cache_path(date_str): return os.path.join(CACHE_DIR, f"{date_str}.json")

def download_session_from_gcs():
    bucket_name = GCS_BUCKET_NAME
    blob_path = "secrets/digest_session.session"
    local_path = "digest_session.session"

    if os.path.exists(local_path):
        print("✅ The session already exists locally")
        return

    print("⬇️ Downloading the session from GCS...")
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    
    if blob.exists():
        blob.download_to_filename(local_path)
        print("✅ The session is loaded")
    else:
        print("❌ The session was not found in GCS")


async def fetch_messages_for_date(date_str):
    date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    all_messages = defaultdict(list)
    async with TelegramClient("digest_session", API_ID, API_HASH) as tg:
        for topic, channels in TOPICS_AND_CHANNELS.items():
            for ch in channels:
                try:
                    entity = await tg.get_entity(ch)
                    history = await tg(GetHistoryRequest(
                        peer=entity,
                        limit=100,
                        offset_date=None,
                        offset_id=0,
                        max_id=0,
                        min_id=0,
                        add_offset=0,
                        hash=0
                    ))
                    for msg in history.messages:
                        if msg.message and msg.date.date() == date_obj:
                            all_messages[topic].append(msg.message.strip())
                except Exception as e:
                    print(f"Channel error {ch}: {e}")
    return all_messages


def cluster_and_summarize(messages_by_topic):
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    result_text = ""

    for topic, messages in messages_by_topic.items():
        if not messages:
            continue

        embeddings = embedder.encode(messages)
        clustering = DBSCAN(eps=0.4, min_samples=2, metric='cosine').fit(embeddings)
        labels = clustering.labels_

        clusters = defaultdict(list)
        for i, label in enumerate(labels):
            clusters[label].append(messages[i])

        result_text += f"\n*{topic.upper()}*\n"
        for label, cluster in clusters.items():
            if label == -1:
                result_text += "\n_Disparate posts:_\n"
            else:
                result_text += f"\n_Cluster #{label} ({len(cluster)} posts):_\n"
            summary = summarize_with_gpt(cluster[:10])
            result_text += f"{summary}\n"
    return result_text.strip()


def summarize_with_gpt(messages):
    prompt = (
        "You're a news analyst. Here are a few posts on the same topic."
        "Make a short and clear summary of this topic in Russian."
        "Highlight the facts, no repetition. Here are the messages:"
        + "\n\n".join(messages)
    )
    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=400
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Error GPT: {e}"


def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text[:4090] + "\n..." if len(text) > 4090 else text,
        "parse_mode": "Markdown"
    }
    r = requests.post(url, json=payload)
    if r.status_code == 200:
        print("📬 The digest has been sent to Telegram.")
    else:
        print("❌ Error when sending to Telegram:", r.text, url, payload)


async def generate_digest_for_date(date_str):
    messages_by_topic = load_cache_from_gcs(date_str)
    if messages_by_topic:
        print(f"✅ Loaded cache from GCS for {date_str}")
    else:
        messages_by_topic = await fetch_messages_for_date(date_str)
        save_cache_to_gcs(date_str, messages_by_topic)
        print(f"✅ Saved cache to GCS for {date_str}")

    digest_text = cluster_and_summarize(messages_by_topic)
    send_to_telegram(digest_text)
