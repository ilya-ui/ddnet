"""Entry point for launching the FastAPI proxy."""
from __future__ import annotations

import os
import uvicorn


def run() -> None:
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "lmarena_proxy.server:app",
        host=host,
        port=port,
        reload=False,
        workers=int(os.getenv("UVICORN_WORKERS", "1")),
    )


if __name__ == "__main__":
    run()
