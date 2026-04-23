from __future__ import annotations

import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path


def setup_logging() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s - %(message)s",
        datefmt="%m-%d %H:%M",
    )


def main() -> int:
    setup_logging()

    base_dir = Path(__file__).resolve().parents[1]
    now = datetime.now()
    date_dir = now.strftime("%m-%d")
    time_prefix = now.strftime("%H-%M")

    logs_dir = base_dir / "logs" / date_dir
    logs_dir.mkdir(parents=True, exist_ok=True)

    log_path = logs_dir / f"{time_prefix}_run_server.log"

    host = os.getenv("APP_HOST", "0.0.0.0")
    port = os.getenv("APP_PORT") or os.getenv("PORT") or "8000"

    cmd = [
        "uvicorn",
        "app.main:app",
        "--host",
        host,
        "--port",
        str(port),
    ]

    env = os.environ.copy()
    with open(log_path, "a", encoding="utf-8") as fp:
        proc = subprocess.Popen(
            cmd,
            cwd=str(base_dir),
            env=env,
            stdout=fp,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )

    logging.info("Server started pid=%s host=%s port=%s", proc.pid, host, port)
    logging.info("Log file: %s", log_path)
    logging.info("Open: http://localhost:%s/", port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
