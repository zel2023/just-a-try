from __future__ import annotations

import os
from dataclasses import dataclass


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    app_host: str
    app_port: int

    openai_base_url: str
    openai_model: str

    ai_name: str
    ai_auto_reply: bool
    ai_context_messages: int
    ai_temperature: float
    ai_max_tokens: int
    ai_queue_max: int
    ai_request_timeout_seconds: float


def load_settings() -> Settings:
    return Settings(
        app_host=os.getenv("APP_HOST", "0.0.0.0"),
        app_port=_env_int("APP_PORT", _env_int("PORT", 8000)),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        ai_name=os.getenv("AI_NAME", "AI").strip() or "AI",
        ai_auto_reply=_env_bool("AI_AUTO_REPLY", True),
        ai_context_messages=_env_int("AI_CONTEXT_MESSAGES", 20),
        ai_temperature=_env_float("AI_TEMPERATURE", 0.7),
        ai_max_tokens=_env_int("AI_MAX_TOKENS", 512),
        ai_queue_max=_env_int("AI_QUEUE_MAX", 50),
        ai_request_timeout_seconds=_env_float("AI_REQUEST_TIMEOUT_SECONDS", 60.0),
    )
