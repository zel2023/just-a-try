from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

import httpx

from app.chat import Room
from app.settings import Settings

logger = logging.getLogger(__name__)


class AIError(RuntimeError):
    pass


class OpenAICompatClient:
    def __init__(self, *, timeout_seconds: float) -> None:
        self._timeout_seconds = timeout_seconds
        self._client: httpx.AsyncClient | None = None

    async def start(self) -> None:
        if self._client is not None:
            return
        self._client = httpx.AsyncClient(timeout=self._timeout_seconds)

    async def close(self) -> None:
        if self._client is None:
            return
        await self._client.aclose()
        self._client = None

    async def chat_completion(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        messages: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
    ) -> str:
        if self._client is None:
            raise AIError("AI client not started")

        base = (base_url or "").rstrip("/")
        if not base:
            raise AIError("base_url is empty")

        if not api_key:
            raise AIError("api_key is empty")

        url = f"{base}/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}"}
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            resp = await self._client.post(url, headers=headers, json=payload)
        except httpx.HTTPError as e:
            raise AIError(f"request failed: {e}") from e

        if resp.status_code >= 400:
            raise AIError(f"bad status {resp.status_code}: {resp.text[:200]}")

        try:
            data = resp.json()
        except ValueError as e:
            raise AIError("invalid json response") from e

        try:
            return str(data["choices"][0]["message"]["content"])
        except Exception as e:
            raise AIError(f"unexpected response shape: {data!r}") from e


def build_ai_messages(*, settings: Settings, room_name: str, history: list[dict[str, Any]]) -> list[dict[str, str]]:
    system_prompt = (
        f"You are {settings.ai_name} in a multi-user chat room named '{room_name}'. "
        "Reply concisely and helpfully. If multiple users speak, address them by name when useful."
    )

    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

    for item in history[-settings.ai_context_messages :]:
        if item.get("type") != "chat":
            continue
        from_user = str(item.get("from") or "")
        text = str(item.get("text") or "")
        if not text:
            continue

        if from_user == settings.ai_name:
            messages.append({"role": "assistant", "content": text})
        else:
            messages.append({"role": "user", "content": f"{from_user}: {text}"})

    return messages


@dataclass(frozen=True)
class AIJob:
    triggered_by: str
    user_text: str
    forced: bool
    api_key: str | None
    base_url: str
    model: str


class RoomAIWorker:
    def __init__(self, *, room: Room, settings: Settings, client: OpenAICompatClient) -> None:
        self._room = room
        self._settings = settings
        self._client = client
        self._queue: asyncio.Queue[AIJob] = asyncio.Queue(maxsize=settings.ai_queue_max)
        self._task: asyncio.Task[None] | None = None

    def start(self) -> None:
        if self._task is not None:
            return
        self._task = asyncio.create_task(self._run(), name=f"ai-worker:{self._room.name}")

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None

    async def enqueue(self, job: AIJob) -> None:
        try:
            self._queue.put_nowait(job)
        except asyncio.QueueFull:
            await self._room.broadcast_system(f"{self._settings.ai_name} is busy; dropped a message")

    async def _run(self) -> None:
        while True:
            job = await self._queue.get()
            try:
                if not job.api_key:
                    if job.forced:
                        echo = (job.user_text or "").strip()
                        echo = echo[:200]
                        await self._room.broadcast_chat(
                            from_username=self._settings.ai_name,
                            text=f"（未配置 API Key，先回声）{echo}",
                        )
                    continue

                history = await self._room.history_snapshot(limit=max(self._settings.ai_context_messages * 2, 50))
                messages = build_ai_messages(settings=self._settings, room_name=self._room.name, history=history)
                reply = await self._client.chat_completion(
                    base_url=job.base_url,
                    api_key=job.api_key,
                    model=job.model,
                    messages=messages,
                    temperature=self._settings.ai_temperature,
                    max_tokens=self._settings.ai_max_tokens,
                )
                reply = (reply or "").strip()
                if not reply:
                    reply = "(empty response)"
                await self._room.broadcast_chat(from_username=self._settings.ai_name, text=reply)
            except AIError as e:
                logger.warning("AIError room=%s by=%s: %s", self._room.name, job.triggered_by, e)
                await self._room.broadcast_system(f"{self._settings.ai_name} error: {e}")
            except Exception:
                logger.exception("AI worker crashed room=%s by=%s", self._room.name, job.triggered_by)
                await self._room.broadcast_system(f"{self._settings.ai_name} error: unexpected error")


class AIResponder:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._lock = asyncio.Lock()
        self._workers: dict[str, RoomAIWorker] = {}
        self._client = OpenAICompatClient(timeout_seconds=settings.ai_request_timeout_seconds)

    async def start(self) -> None:
        await self._client.start()
        logger.info("AI client started auto_reply=%s", self._settings.ai_auto_reply)

    async def close(self) -> None:
        async with self._lock:
            workers = list(self._workers.values())
            self._workers.clear()

        for worker in workers:
            await worker.stop()

        await self._client.close()

    async def enqueue(
        self,
        *,
        room: Room,
        triggered_by: str,
        user_text: str,
        forced: bool,
        api_key: str | None,
        base_url: str,
        model: str,
    ) -> None:
        worker = await self._get_worker(room)
        await worker.enqueue(
            AIJob(
                triggered_by=triggered_by,
                user_text=user_text,
                forced=forced,
                api_key=api_key,
                base_url=base_url,
                model=model,
            )
        )

    async def _get_worker(self, room: Room) -> RoomAIWorker:
        async with self._lock:
            worker = self._workers.get(room.name)
            if worker is None:
                worker = RoomAIWorker(room=room, settings=self._settings, client=self._client)
                worker.start()
                self._workers[room.name] = worker
            return worker
