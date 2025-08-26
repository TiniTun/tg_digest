from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

from .digest_pipeline import download_session_from_gcs, generate_digest_for_date


@asynccontextmanager
async def lifespan(app: FastAPI):
    download_session_from_gcs()
    yield


app = FastAPI(lifespan=lifespan)


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
