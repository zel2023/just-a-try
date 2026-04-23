from __future__ import annotations

import ipaddress
from datetime import datetime
from urllib.parse import urlparse


def now_ts() -> str:
    return datetime.now().strftime("%m-%d %H:%M")


def normalize_room(room: str | None) -> str:
    value = (room or "").strip()
    if not value:
        return "lobby"
    value = value[:32]
    return value


def normalize_username(username: str | None) -> str:
    value = (username or "").strip()
    if not value:
        return "guest"
    value = value.replace("\n", " ").replace("\r", " ").strip()
    return value[:32]


def normalize_openai_api_key(api_key: str | None) -> str | None:
    value = (api_key or "").strip()
    if not value:
        return None
    return value[:256]


def normalize_openai_model(model: str | None, *, default: str) -> str:
    value = (model or "").strip()
    if not value:
        return default
    return value[:64]


def validate_openai_base_url(base_url: str | None, *, default: str) -> str:
    value = (base_url or "").strip()
    if not value:
        value = default

    if len(value) > 200:
        raise ValueError("base_url too long")

    parsed = urlparse(value)
    if parsed.scheme != "https":
        raise ValueError("base_url must start with https://")
    if not parsed.netloc:
        raise ValueError("base_url missing host")

    host = parsed.hostname or ""
    host = host.strip().lower()
    if host in {"localhost"} or host.endswith(".local"):
        raise ValueError("base_url host not allowed")

    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        ip = None

    if ip is not None:
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            raise ValueError("base_url IP not allowed")

    return value.rstrip("/")
