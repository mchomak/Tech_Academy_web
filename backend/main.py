import os
import logging

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

app = FastAPI(title="F5 Academy Lead API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

logger = logging.getLogger("lead_api")


class LeadIn(BaseModel):
    name: str
    phone: str
    course: str | None = None
    email: str | None = None


@app.post("/api/lead")
async def create_lead(lead: LeadIn):
    lines = [
        "\U0001f4e9 <b>Новая заявка с сайта</b>",
        f"<b>Имя:</b> {lead.name}",
        f"<b>Телефон:</b> {lead.phone}",
    ]
    if lead.course:
        lines.append(f"<b>Курс:</b> {lead.course}")
    if lead.email:
        lines.append(f"<b>Email:</b> {lead.email}")

    text = "\n".join(lines)

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram credentials missing – lead saved but not sent")
        return {"ok": True, "telegram": False}

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
    }

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(url, json=payload)

    if resp.status_code != 200:
        logger.error("Telegram API error: %s", resp.text)
        raise HTTPException(status_code=502, detail="Telegram notification failed")

    return {"ok": True, "telegram": True}
