from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from fastapi import WebSocket

from app.utils import now_ts, normalize_username

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Client:
    username: str


class Room:
    def __init__(self, name: str, *, history_limit: int = 200) -> None:
        self.name = name
        self._history_limit = history_limit
        self._lock = asyncio.Lock()
        self._clients: dict[WebSocket, Client] = {}
        self._history: list[dict[str, Any]] = []

    async def connect(self, websocket: WebSocket, requested_username: str) -> str:
        await websocket.accept()

        username = normalize_username(requested_username)
        async with self._lock:
            username = self._dedupe_username_locked(username)
            self._clients[websocket] = Client(username=username)

            history_snapshot = list(self._history)

        if history_snapshot:
            await self._safe_send_json(websocket, {"type": "history", "room": self.name, "messages": history_snapshot})

        await self.broadcast_system(f"{username} joined")
        await self.broadcast_presence()
        return username

    async def disconnect(self, websocket: WebSocket) -> str | None:
        async with self._lock:
            client = self._clients.pop(websocket, None)
        if not client:
            return None
        await self.broadcast_system(f"{client.username} left")
        await self.broadcast_presence()
        return client.username

    async def broadcast_chat(self, *, from_username: str, text: str) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": "chat",
            "room": self.name,
            "from": from_username,
            "text": text,
            "ts": now_ts(),
        }
        await self._append_history(payload)
        await self.broadcast(payload)
        return payload

    async def broadcast_system(self, text: str) -> None:
        payload: dict[str, Any] = {
            "type": "system",
            "room": self.name,
            "text": text,
            "ts": now_ts(),
        }
        await self._append_history(payload)
        await self.broadcast(payload)

    async def broadcast_presence(self) -> None:
        async with self._lock:
            users = sorted({client.username for client in self._clients.values()})

        payload: dict[str, Any] = {
            "type": "presence",
            "room": self.name,
            "users": users,
            "count": len(users),
            "ts": now_ts(),
        }
        await self.broadcast(payload)

    async def broadcast(self, payload: dict[str, Any]) -> None:
        async with self._lock:
            websockets = list(self._clients.keys())

        if not websockets:
            return

        results = await asyncio.gather(
            *(self._safe_send_json(ws, payload) for ws in websockets),
            return_exceptions=True,
        )

        stale: list[WebSocket] = [ws for ws, ok in zip(websockets, results, strict=True) if ok is False]
        if stale:
            async with self._lock:
                for ws in stale:
                    self._clients.pop(ws, None)

    def users_snapshot(self) -> list[str]:
        return sorted({client.username for client in self._clients.values()})

    async def history_snapshot(self, *, limit: int | None = None) -> list[dict[str, Any]]:
        async with self._lock:
            if limit is None:
                return list(self._history)
            if limit <= 0:
                return []
            return list(self._history[-limit:])

    async def _append_history(self, payload: dict[str, Any]) -> None:
        async with self._lock:
            self._history.append(payload)
            if len(self._history) > self._history_limit:
                self._history = self._history[-self._history_limit :]

    def _dedupe_username_locked(self, username: str) -> str:
        existing = {client.username for client in self._clients.values()}
        if username not in existing:
            return username

        for i in range(2, 1000):
            candidate = f"{username}-{i}"
            if candidate not in existing:
                return candidate
        return f"{username}-999"

    async def _safe_send_json(self, websocket: WebSocket, payload: dict[str, Any]) -> bool:
        try:
            await websocket.send_json(payload)
            return True
        except Exception:
            return False


class ChatHub:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._rooms: dict[str, Room] = {}

    async def get_room(self, room_name: str) -> Room:
        async with self._lock:
            room = self._rooms.get(room_name)
            if room is None:
                room = Room(room_name)
                self._rooms[room_name] = room
                logger.info("Room created: %s", room_name)
            return room
