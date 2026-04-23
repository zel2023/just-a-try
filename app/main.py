from __future__ import annotations

import json
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.ai import AIResponder
from app.chat import ChatHub
from app.settings import Settings, load_settings
from app.utils import (
    normalize_openai_api_key,
    normalize_openai_model,
    normalize_room,
    normalize_username,
    validate_openai_base_url,
)


def setup_logging() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        datefmt="%m-%d %H:%M",
    )


load_dotenv()
setup_logging()
logger = logging.getLogger(__name__)
settings: Settings = load_settings()

BASE_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = BASE_DIR / "static"

hub = ChatHub()
ai = AIResponder(settings)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await ai.start()
    yield
    await ai.close()


app = FastAPI(title="Chat AI Web", lifespan=lifespan)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/config")
async def config() -> dict[str, object]:
    return {
        "ai_name": settings.ai_name,
        "ai_auto_reply": settings.ai_auto_reply,
        "openai_base_url": settings.openai_base_url,
        "openai_model": settings.openai_model,
    }


@app.websocket("/ws")
async def ws_endpoint(
    websocket: WebSocket,
    username: str = Query(default="guest"),
    room: str = Query(default="lobby"),
) -> None:
    room_name = normalize_room(room)
    requested_username = normalize_username(username)
    if requested_username == settings.ai_name:
        requested_username = f"{requested_username}-user"

    user_api_key: str | None = None
    user_base_url: str = settings.openai_base_url
    user_model: str = settings.openai_model

    room_obj = await hub.get_room(room_name)
    final_username = await room_obj.connect(websocket, requested_username)
    logger.info("WS connect room=%s user=%s", room_name, final_username)
    await websocket.send_json(
        {
            "type": "welcome",
            "room": room_name,
            "username": final_username,
            "ai_name": settings.ai_name,
            "ai_auto_reply": settings.ai_auto_reply,
            "openai_base_url": user_base_url,
            "openai_model": user_model,
        }
    )

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                data = {"type": "chat", "text": raw}

            if not isinstance(data, dict):
                continue

            msg_type = str(data.get("type") or "chat")
            if msg_type == "config":
                try:
                    user_api_key = normalize_openai_api_key(str(data.get("openai_api_key") or ""))
                    user_base_url = validate_openai_base_url(
                        str(data.get("openai_base_url") or ""),
                        default=settings.openai_base_url,
                    )
                    user_model = normalize_openai_model(
                        str(data.get("openai_model") or ""),
                        default=settings.openai_model,
                    )
                except ValueError as e:
                    await websocket.send_json({"type": "config_ack", "ok": False, "error": str(e)})
                    continue

                await websocket.send_json(
                    {
                        "type": "config_ack",
                        "ok": True,
                        "has_key": bool(user_api_key),
                        "openai_base_url": user_base_url,
                        "openai_model": user_model,
                    }
                )
                continue

            if msg_type != "chat":
                continue

            text = str(data.get("text") or "").strip()
            if not text:
                continue

            cleaned = text
            force_ai = False
            for prefix in ("/ai ", "@ai "):
                if cleaned.lower().startswith(prefix):
                    cleaned = cleaned[len(prefix) :].strip()
                    force_ai = True
                    break

            if not cleaned:
                continue

            await room_obj.broadcast_chat(from_username=final_username, text=cleaned)

            if force_ai or (settings.ai_auto_reply and user_api_key):
                await ai.enqueue(
                    room=room_obj,
                    triggered_by=final_username,
                    user_text=cleaned,
                    forced=force_ai,
                    api_key=user_api_key,
                    base_url=user_base_url,
                    model=user_model,
                )

    except WebSocketDisconnect:
        logger.info("WS disconnect room=%s user=%s", room_name, final_username)
    except Exception:
        logger.exception("WS error room=%s user=%s", room_name, final_username)
    finally:
        await room_obj.disconnect(websocket)
