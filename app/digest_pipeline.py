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

from .config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, OPENAI_API_KEY, API_ID, API_HASH, TOPICS_AND_CHANNELS

CACHE_TIME = 2  # hours
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)
client = OpenAI(api_key=OPENAI_API_KEY)


def cache_path(date_str): return os.path.join(CACHE_DIR, f"{date_str}.json")


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
        "Make a short and clear summary of this topic in English in the Australian manner."
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
    # Cache
    path = cache_path(date_str)
    if os.path.exists(path) and (
        datetime.now() - datetime.fromtimestamp(os.path.getmtime(path))
    ) < timedelta(hours=CACHE_TIME):
        with open(path, "r", encoding="utf-8") as f:
            messages_by_topic = json.load(f)
    else:
        messages_by_topic = await fetch_messages_for_date(date_str)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(messages_by_topic, f, ensure_ascii=False, indent=2)

    digest_text = cluster_and_summarize(messages_by_topic)
    send_to_telegram(digest_text)
