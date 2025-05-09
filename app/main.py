from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from datetime import datetime
import asyncio

from .digest_pipeline import generate_digest_for_date

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Telegram Digest Cloud Run is live."}

@app.post("/run")
async def run_digest(_: Request):
    date_str = datetime.now().date().isoformat()
    await generate_digest_for_date(date_str)
    return PlainTextResponse(f"✅ Digest generated and sent for {date_str}")

@app.get("/run/{date_str}")
async def run_digest_for_date(date_str: str):
    await generate_digest_for_date(date_str)
    return PlainTextResponse(f"✅ Digest generated and sent for {date_str}")
