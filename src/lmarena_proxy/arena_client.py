"""Low-level client for interacting with the canary.lmarena.ai API."""
from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Dict, Generator, Iterable, List, Optional, Tuple

from curl_cffi import requests
from curl_cffi.requests import RequestsError

from .config import settings
from .cookie_pool import CookiePool
from .models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    ChatMessageContentPart,
    Choice,
    DeltaMessage,
    ModelItem,
    ModelListResponse,
)

_logger = logging.getLogger(__name__)

MODEL_REGISTRY: Dict[str, Dict[str, str]] = {
    "gemini-2.5-pro-preview-05-06": {
        "id": "0337ee08-8305-40c0-b820-123ad42b60cf",
        "type": "chat",
        "display_name": "Gemini 2.5 Pro (preview 2025-05-06)",
    },
}

MODEL_ALIASES: Dict[str, str] = {
    "gemini-2.5-pro": "gemini-2.5-pro-preview-05-06",
    "gemini-2.5-pro-preview": "gemini-2.5-pro-preview-05-06",
    "gemini-2.5-pro-preview-05-06": "gemini-2.5-pro-preview-05-06",
}

RESPONSE_ID_FORMAT = "chatcmpl-%s"


class ArenaAPIError(RuntimeError):
    """Server side error from LMArena."""

    def __init__(self, message: str, *, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass
class SSEChunk:
    text: Optional[str]
    continue_stream: bool


class ArenaClient:
    """Wrapper around the LMArena stream API."""

    def __init__(self, cookie_pool: CookiePool) -> None:
        self._cookie_pool = cookie_pool

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def list_models(self) -> ModelListResponse:
        items = [ModelItem(id=alias) for alias in sorted(MODEL_ALIASES.keys())]
        return ModelListResponse(data=items)

    def chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        resolved_model = self._resolve_model(request.model)
        payload = self._build_payload(request.messages, resolved_model)
        cookie = self._cookie_pool.next()
        response_id = RESPONSE_ID_FORMAT % uuid.uuid4().hex
        accumulated: List[str] = []

        for chunk in self._stream_payload(payload, cookie):
            if chunk.text:
                accumulated.append(chunk.text)
            if not chunk.continue_stream:
                break

        assistant_message = "".join(accumulated)
        created_ts = int(time.time())
        choice = Choice(
            index=0,
            message=ChatMessage(role="assistant", content=assistant_message),
            finish_reason="stop",
        )
        return ChatCompletionResponse(
            id=response_id,
            object="chat.completion",
            created=created_ts,
            model=resolved_model,
            choices=[choice],
        )

    def chat_completion_stream(self, request: ChatCompletionRequest) -> Generator[str, None, None]:
        resolved_model = self._resolve_model(request.model)
        payload = self._build_payload(request.messages, resolved_model)
        cookie = self._cookie_pool.next()
        created_ts = int(time.time())
        response_id = RESPONSE_ID_FORMAT % uuid.uuid4().hex
        role_sent = False

        try:
            for chunk in self._stream_payload(payload, cookie):
                if chunk.text:
                    delta = DeltaMessage(
                        role="assistant" if not role_sent else None,
                        content=chunk.text,
                    )
                    role_sent = True
                    packet = {
                        "id": response_id,
                        "object": "chat.completion.chunk",
                        "created": created_ts,
                        "model": resolved_model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": delta.model_dump(exclude_none=True),
                                "finish_reason": None,
                            }
                        ],
                    }
                    yield f"data: {json.dumps(packet, ensure_ascii=False)}\n\n"
                if not chunk.continue_stream:
                    final_packet = {
                        "id": response_id,
                        "object": "chat.completion.chunk",
                        "created": created_ts,
                        "model": resolved_model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {},
                                "finish_reason": "stop",
                            }
                        ],
                    }
                    yield f"data: {json.dumps(final_packet, ensure_ascii=False)}\n\n"
                    break
        finally:
            yield "data: [DONE]\n\n"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _resolve_model(self, requested_model: str) -> str:
        key = requested_model.strip()
        canonical = MODEL_ALIASES.get(key, key)
        if canonical not in MODEL_REGISTRY:
            raise ArenaAPIError(f"Model '{requested_model}' is not supported by this bridge.")
        return canonical

    def _build_payload(self, messages: Iterable[ChatMessage], model_name: str) -> Dict[str, object]:
        model_info = MODEL_REGISTRY[model_name]
        evaluation_id = uuid.uuid4().hex
        arena_messages: List[Dict[str, object]] = []
        previous_message_id: Optional[str] = None
        last_user_message_id: Optional[str] = None

        for message in messages:
            message_id = uuid.uuid4().hex
            parent_ids: List[str] = []
            if previous_message_id:
                parent_ids = [previous_message_id]
            role = message.role
            if role == "system":
                role = "user"
            content = self._coerce_message_content(message.content)
            model_id = model_info["id"] if role == "assistant" else None
            arena_messages.append(
                {
                    "id": message_id,
                    "role": role,
                    "content": content,
                    "experimental_attachments": [],
                    "parentMessageIds": parent_ids,
                    "participantPosition": "a",
                    "modelId": model_id,
                    "evaluationSessionId": evaluation_id,
                    "status": "pending",
                    "failureReason": None,
                }
            )
            previous_message_id = message_id
            if role == "user":
                last_user_message_id = message_id

        if last_user_message_id is None:
            raise ArenaAPIError("Conversation must include at least one user message.")

        model_message_id = uuid.uuid4().hex
        arena_messages.append(
            {
                "id": model_message_id,
                "role": "assistant",
                "content": "",
                "experimental_attachments": [],
                "parentMessageIds": [previous_message_id] if previous_message_id else [],
                "participantPosition": "a",
                "modelId": model_info["id"],
                "evaluationSessionId": evaluation_id,
                "status": "pending",
                "failureReason": None,
            }
        )

        payload = {
            "id": evaluation_id,
            "mode": "direct",
            "modelAId": model_info["id"],
            "userMessageId": last_user_message_id,
            "modelAMessageId": model_message_id,
            "messages": arena_messages,
            "modality": "chat",
        }
        return payload

    def _coerce_message_content(self, content: object) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: List[str] = []
            for entry in content:
                if isinstance(entry, ChatMessageContentPart):
                    if entry.type == "text" and entry.text:
                        parts.append(entry.text)
                elif isinstance(entry, dict):
                    if entry.get("type") == "text" and entry.get("text"):
                        parts.append(str(entry["text"]))
            return "\n".join(parts)
        return str(content)

    def _request_headers(self, cookie_value: str) -> Dict[str, str]:
        cookie = f"cf_clearance={settings.cf_clearance}; arena-auth-prod-v1={cookie_value}"
        return {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "text/plain;charset=UTF-8",
            "origin": settings.api_base_url,
            "priority": "u=1, i",
            "referer": f"{settings.api_base_url}/",
            "sec-ch-ua": '"Microsoft Edge";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            "sec-ch-ua-arch": '"arm"',
            "sec-ch-ua-bitness": '"64"',
            "sec-ch-ua-full-version": '"137.0.3296.52"',
            "sec-ch-ua-full-version-list": '"Microsoft Edge";v="137.0.3296.52", "Chromium";v="137.0.7151.56", "Not/A)Brand";v="24.0.0.0"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-model": '""',
            "sec-ch-ua-platform": '"macOS"',
            "sec-ch-ua-platform-version": '"15.5.0"',
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            "cookie": cookie,
        }

    def _stream_payload(self, payload: Dict[str, object], cookie_value: str) -> Generator[SSEChunk, None, None]:
        url = f"{settings.api_base_url}/api/stream/create-evaluation"
        data = json.dumps(payload, ensure_ascii=False)
        headers = self._request_headers(cookie_value)
        params = {
            "impersonate": settings.impersonate,
            "timeout": settings.request_timeout,
        }
        if settings.proxy_url:
            params["proxies"] = {"https": settings.proxy_url, "http": settings.proxy_url}

        try:
            response = requests.post(
                url,
                data=data.encode("utf-8"),
                headers=headers,
                stream=True,
                impersonate=settings.impersonate,
                timeout=settings.request_timeout,
                proxies=params.get("proxies"),
            )
        except RequestsError as exc:
            raise ArenaAPIError(f"Failed to reach LMArena: {exc}") from exc

        if response.status_code != 200:
            body_preview = response.text[:500]
            raise ArenaAPIError(
                f"LMArena returned HTTP {response.status_code}: {body_preview}",
                status_code=response.status_code,
            )

        for raw_line in response.iter_lines(decode_unicode=True):
            if raw_line is None:
                continue
            line = raw_line.strip()
            if not line:
                continue
            if not line.startswith("data:"):
                continue
            payload_text = line[5:].strip()
            if not payload_text:
                continue
            chunk = self._parse_stream_payload(payload_text)
            if chunk is None:
                continue
            yield chunk
            if not chunk.continue_stream:
                break

        response.close()

    def _parse_stream_payload(self, payload: str) -> Optional[SSEChunk]:
        if payload == "[DONE]":
            return SSEChunk(text=None, continue_stream=False)
        if payload.startswith("{"):
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                _logger.debug("Skipping non-JSON stream payload: %s", payload)
                return None
            message = data.get("message") or data.get("error")
            if message:
                raise ArenaAPIError(str(message))
            return None

        if ":" not in payload:
            _logger.debug("Unexpected stream frame: %s", payload)
            return None

        prefix, content = payload.split(":", 1)
        prefix = prefix.strip()
        content = content.strip()

        if prefix == "a0":
            text = self._unquote_text(content)
            return SSEChunk(text=text, continue_stream=True)
        if prefix in {"ae", "ad"}:
            return SSEChunk(text=None, continue_stream=False)
        if prefix in {"af", "cookie"}:
            return None

        _logger.debug("Ignoring stream prefix %s", prefix)
        return None

    def _unquote_text(self, value: str) -> str:
        if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value[1:-1]
        return value


_client_instance: Optional[ArenaClient] = None


def get_client() -> ArenaClient:
    global _client_instance
    if _client_instance is None:
        _client_instance = ArenaClient(CookiePool(settings.arena_cookies))
    return _client_instance
