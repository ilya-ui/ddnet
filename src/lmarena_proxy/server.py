"""FastAPI application exposing OpenAI compatible routes."""
from __future__ import annotations

import logging

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.concurrency import run_in_threadpool

from .arena_client import ArenaAPIError, get_client
from .config import settings
from .models import ChatCompletionRequest

logger = logging.getLogger(__name__)

app = FastAPI(title="LMArena Gemini Proxy", version="0.1.0")


def _check_auth(request: Request) -> None:
    if not settings.auth_secret:
        return
    header = request.headers.get("Authorization")
    if not header or not header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = header.split(" ", 1)[1].strip()
    if token != settings.auth_secret:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid bearer token")


def require_auth(request: Request) -> None:
    _check_auth(request)


@app.get("/health", dependencies=[Depends(require_auth)])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/models", dependencies=[Depends(require_auth)])
async def list_models() -> JSONResponse:
    client = get_client()
    models = client.list_models()
    return JSONResponse(models.model_dump())


@app.post("/v1/chat/completions", dependencies=[Depends(require_auth)])
async def chat_completions(request: ChatCompletionRequest) -> JSONResponse | StreamingResponse:
    client = get_client()
    try:
        if request.stream:
            stream_generator = await run_in_threadpool(client.chat_completion_stream, request)
            return StreamingResponse(stream_generator, media_type="text/event-stream")
        response = await run_in_threadpool(client.chat_completion, request)
        return JSONResponse(response.model_dump())
    except ArenaAPIError as exc:
        logger.warning("Arena API error: %s", exc)
        status_code = exc.status_code or status.HTTP_502_BAD_GATEWAY
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
