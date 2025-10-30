"""Asynchronous WebSocket relay server for the Phone ↔ PC messenger.

Run with:
    python relay_server.py --host 0.0.0.0 --port 8765
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Deque, Dict, Optional, Set

import websockets
from websockets.server import WebSocketServerProtocol


@dataclass
class ClientInfo:
    websocket: WebSocketServerProtocol
    name: Optional[str] = None


class RelayServer:
    """Simple WebSocket relay with in-memory message history."""

    def __init__(self, history_limit: int = 200) -> None:
        self.clients: Dict[WebSocketServerProtocol, ClientInfo] = {}
        self.history: Deque[dict] = deque(maxlen=history_limit)
        self._lock = asyncio.Lock()

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    async def register(self, websocket: WebSocketServerProtocol) -> None:
        async with self._lock:
            self.clients[websocket] = ClientInfo(websocket=websocket)
        logging.info("Client connected from %s", websocket.remote_address)
        if self.history:
            await self._send_json(
                websocket,
                {
                    "type": "history",
                    "messages": list(self.history),
                    "timestamp": self._timestamp(),
                },
            )

    async def unregister(self, websocket: WebSocketServerProtocol) -> None:
        async with self._lock:
            client = self.clients.pop(websocket, None)
        if client and client.name:
            await self.broadcast_system(f"{client.name} отключился.", exclude={websocket})
        logging.info("Client disconnected %s", websocket.remote_address)

    async def set_name(self, websocket: WebSocketServerProtocol, name: str) -> None:
        async with self._lock:
            client = self.clients.get(websocket)
            if client is None:
                return
            previous_name = client.name
            client.name = name
        if previous_name and previous_name != name:
            await self.broadcast_system(
                f"{previous_name} теперь известен как {name}.", exclude={websocket}
            )
        await self._send_system(websocket, f"Вы подключены как {name}.")
        await self.broadcast_system(f"{name} подключился.", exclude={websocket})

    async def broadcast(self, payload: dict, exclude: Optional[Set[WebSocketServerProtocol]] = None) -> None:
        if exclude is None:
            exclude = set()
        targets = [client for client in list(self.clients.keys()) if client not in exclude]
        if not targets:
            return
        message = json.dumps(payload)
        await asyncio.gather(*(self._safe_send(ws, message) for ws in targets), return_exceptions=True)

    async def broadcast_system(self, text: str, exclude: Optional[Set[WebSocketServerProtocol]] = None) -> None:
        payload = {
            "type": "system",
            "content": text,
            "timestamp": self._timestamp(),
        }
        await self.broadcast(payload, exclude=exclude)

    async def _send_system(self, websocket: WebSocketServerProtocol, text: str) -> None:
        await self._send_json(
            websocket,
            {
                "type": "system",
                "content": text,
                "timestamp": self._timestamp(),
            },
        )

    async def _send_error(self, websocket: WebSocketServerProtocol, code: str, message: str) -> None:
        await self._send_json(
            websocket,
            {
                "type": "error",
                "code": code,
                "message": message,
                "timestamp": self._timestamp(),
            },
        )

    async def _send_json(self, websocket: WebSocketServerProtocol, payload: dict) -> None:
        try:
            await websocket.send(json.dumps(payload))
        except Exception as exc:  # pragma: no cover - defensive logging
            logging.warning("Failed to send payload to %s: %s", websocket.remote_address, exc)

    async def _safe_send(self, websocket: WebSocketServerProtocol, message: str) -> None:
        try:
            await websocket.send(message)
        except Exception as exc:  # pragma: no cover - defensive logging
            logging.warning("Failed to broadcast to %s: %s", websocket.remote_address, exc)

    async def handle_message(self, websocket: WebSocketServerProtocol, data: dict) -> None:
        msg_type = data.get("type")
        if msg_type == "hello":
            name = (data.get("name") or "").strip()
            if not name:
                await self._send_error(websocket, "invalid_name", "Имя не может быть пустым.")
                return
            await self.set_name(websocket, name)
        elif msg_type == "message":
            content = (data.get("content") or "").strip()
            if not content:
                await self._send_error(websocket, "empty_message", "Нельзя отправить пустое сообщение.")
                return
            async with self._lock:
                client = self.clients.get(websocket)
                sender = client.name if client else None
            if not sender:
                await self._send_error(websocket, "not_identified", "Укажите имя перед отправкой сообщений.")
                return
            payload = {
                "type": "message",
                "sender": sender,
                "content": content,
                "timestamp": self._timestamp(),
            }
            self.history.append(payload)
            await self.broadcast(payload)
        else:
            await self._send_error(websocket, "unknown_type", f"Неизвестный тип сообщения: {msg_type}")

    async def handler(self, websocket: WebSocketServerProtocol) -> None:
        await self.register(websocket)
        try:
            async for raw in websocket:
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    await self._send_error(websocket, "invalid_json", "Некорректный формат JSON.")
                    continue
                await self.handle_message(websocket, data)
        except websockets.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)


async def run_server(host: str, port: int, history_limit: int) -> None:
    server = RelayServer(history_limit=history_limit)
    logging.info("Starting relay server on %s:%s", host, port)
    async with websockets.serve(server.handler, host, port, ping_interval=20, ping_timeout=20):
        logging.info("Relay server is running. Press Ctrl+C to stop.")
        stop_event = asyncio.Event()
        try:
            await stop_event.wait()
        except asyncio.CancelledError:
            logging.info("Stopping relay server...")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Phone ↔ PC messenger relay server")
    parser.add_argument("--host", default="0.0.0.0", help="Host/IP address to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8765, help="Port to listen on (default: 8765)")
    parser.add_argument(
        "--history-limit",
        type=int,
        default=200,
        help="Number of recent messages to keep in memory (default: 200)",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
    args = parse_args()
    try:
        asyncio.run(run_server(args.host, args.port, args.history_limit))
    except KeyboardInterrupt:
        logging.info("Server interrupted by user. Bye!")


if __name__ == "__main__":
    main()
