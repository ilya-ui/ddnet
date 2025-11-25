"""Entry point for launching the FastAPI proxy."""
from __future__ import annotations

import os
import sys
import uvicorn

from .config import get_settings


def _pause_if_needed() -> None:
    if os.getenv("LMARENA_PROXY_NO_PAUSE") == "1":
        return
    try:
        input("Press Enter to exit...")
    except EOFError:
        pass


def run() -> None:
    try:
        cfg = get_settings()
    except RuntimeError as exc:
        print(f"[CONFIG ERROR] {exc}")
        print("Please edit the .env file with cf_clearance and arena cookies as documented in README.md.")
        _pause_if_needed()
        return

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    workers = int(os.getenv("UVICORN_WORKERS", "1"))

    print(
        f"Starting LMArena Gemini Proxy on {host}:{port} (workers={workers}, cookies={len(cfg.arena_cookies)})"
    )
    try:
        uvicorn.run(
            "lmarena_proxy.server:app",
            host=host,
            port=port,
            reload=False,
            workers=workers,
        )
    except Exception as exc:  # pragma: no cover - runtime safety
        print(f"[ERROR] Failed to start server: {exc}")
        _pause_if_needed()
        raise


if __name__ == "__main__":  # pragma: no cover - CLI entry
    try:
        run()
    except KeyboardInterrupt:
        print("\nServer interrupted by user.")
        sys.exit(0)
