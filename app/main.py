"""Kivy client application for the Phone ↔ PC messenger."""
from __future__ import annotations

import asyncio
import json
import queue
import threading
from datetime import datetime
from random import randint
from typing import Any, Optional

import websockets
from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.textinput import TextInput


class NetworkClient:
    """Manages the WebSocket connection in a background thread."""

    def __init__(
        self,
        uri: str,
        display_name: str,
        message_queue: queue.Queue,
        status_queue: queue.Queue,
    ) -> None:
        self.uri = uri
        self.display_name = display_name
        self.message_queue = message_queue
        self.status_queue = status_queue
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.thread: Optional[threading.Thread] = None
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.stop_event = threading.Event()

    def start(self) -> None:
        if self.thread and self.thread.is_alive():
            return
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self) -> None:
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._run_client())
        finally:
            pending = asyncio.all_tasks(self.loop)
            for task in pending:
                task.cancel()
            if pending:
                try:
                    self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                except Exception:
                    pass
            self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            self.loop.close()

    async def _run_client(self) -> None:
        backoff = 1
        while not self.stop_event.is_set():
            self.status_queue.put(("connecting", None))
            try:
                async with websockets.connect(
                    self.uri,
                    ping_interval=20,
                    ping_timeout=20,
                    close_timeout=5,
                ) as websocket:
                    self.ws = websocket
                    await websocket.send(json.dumps({"type": "hello", "name": self.display_name}))
                    self.status_queue.put(("connected", None))
                    backoff = 1
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                        except json.JSONDecodeError:
                            continue
                        self.message_queue.put(data)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                if self.stop_event.is_set():
                    break
                self.status_queue.put(("disconnected", str(exc)))
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 10)
            finally:
                self.ws = None
        self.status_queue.put(("stopped", None))

    def send_message(self, content: str) -> bool:
        content = (content or "").strip()
        if not content or not self.loop or not self.ws:
            return False
        payload = json.dumps({"type": "message", "content": content})
        try:
            asyncio.run_coroutine_threadsafe(self._send(payload), self.loop)
            return True
        except RuntimeError:
            return False

    async def _send(self, payload: str) -> None:
        if self.ws:
            await self.ws.send(payload)

    def stop(self) -> None:
        self.stop_event.set()
        if self.loop and self.loop.is_running():
            if self.ws:
                try:
                    asyncio.run_coroutine_threadsafe(self.ws.close(), self.loop)
                except RuntimeError:
                    pass
            self.loop.call_soon_threadsafe(lambda: None)
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
            self.thread = None
        self.ws = None
        self.loop = None


class SetupScreen(Screen):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.name = "setup"
        self.app: Optional[MessengerApp] = None

        root = BoxLayout(orientation="vertical", padding=dp(18), spacing=dp(12))

        title = Label(text="Phone ↔ PC Messenger", font_size="22sp", size_hint_y=None, height=dp(40))
        root.add_widget(title)

        description = Label(
            text=(
                "Введите отображаемое имя, адрес сервера и порт.\n"
                "Сервер должен работать на ПК или другом устройстве."
            ),
            size_hint_y=None,
            height=dp(70),
        )
        description.bind(size=lambda inst, value: setattr(inst, "text_size", value))
        root.add_widget(description)

        root.add_widget(Label(text="Имя в чате", size_hint_y=None, height=dp(24)))
        self.display_name_input = TextInput(
            text=f"User-{randint(100, 999)}",
            multiline=False,
            size_hint_y=None,
            height=dp(42),
        )
        root.add_widget(self.display_name_input)

        root.add_widget(Label(text="Адрес сервера (IP или hostname)", size_hint_y=None, height=dp(24)))
        self.host_input = TextInput(
            text="127.0.0.1",
            multiline=False,
            size_hint_y=None,
            height=dp(42),
        )
        root.add_widget(self.host_input)

        root.add_widget(Label(text="Порт", size_hint_y=None, height=dp(24)))
        self.port_input = TextInput(
            text="8765",
            multiline=False,
            size_hint_y=None,
            height=dp(42),
            input_filter="int",
        )
        root.add_widget(self.port_input)

        self.error_label = Label(
            text="",
            color=(1, 0, 0, 1),
            size_hint_y=None,
            height=dp(24),
        )
        root.add_widget(self.error_label)

        connect_button = Button(text="Подключиться", size_hint_y=None, height=dp(48))
        connect_button.bind(on_press=self._on_connect)
        root.add_widget(connect_button)

        root.add_widget(Label(size_hint=(1, 1)))
        self.add_widget(root)

    def set_app(self, app: "MessengerApp") -> None:
        self.app = app

    def _on_connect(self, *_args: Any) -> None:
        if not self.app:
            return
        display_name = self.display_name_input.text.strip()
        host = self.host_input.text.strip()
        port_value = self.port_input.text.strip() or "8765"

        if not display_name:
            self.error_label.text = "Введите имя."
            return
        if not host:
            self.error_label.text = "Введите адрес сервера."
            return
        try:
            port = int(port_value)
        except ValueError:
            self.error_label.text = "Некорректный порт."
            return

        self.error_label.text = ""
        self.app.start_chat(display_name, host, port)


class ChatScreen(Screen):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.name = "chat"
        self.app: Optional[MessengerApp] = None
        self.display_name: str = ""

        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10))

        header = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(34), spacing=dp(10))
        self.status_label = Label(text="Не подключено", halign="left", valign="middle")
        self.status_label.bind(size=lambda inst, value: setattr(inst, "text_size", value))
        header.add_widget(self.status_label)
        disconnect_button = Button(text="Отключиться", size_hint=(None, 1), width=dp(130))
        disconnect_button.bind(on_press=self._on_disconnect)
        header.add_widget(disconnect_button)
        root.add_widget(header)

        self.messages_display = TextInput(
            readonly=True,
            cursor_blink=False,
            size_hint=(1, 1),
            background_color=(0.97, 0.97, 0.97, 1),
            foreground_color=(0.05, 0.05, 0.05, 1),
            font_size="16sp",
        )
        root.add_widget(self.messages_display)

        input_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(48), spacing=dp(10))
        self.message_input = TextInput(
            multiline=False,
            hint_text="Введите сообщение",
            size_hint=(1, 1),
        )
        self.message_input.bind(on_text_validate=self._on_send)
        send_button = Button(text="Отправить", size_hint=(None, 1), width=dp(120))
        send_button.bind(on_press=self._on_send)
        input_row.add_widget(self.message_input)
        input_row.add_widget(send_button)
        root.add_widget(input_row)

        self.add_widget(root)

    def set_app(self, app: "MessengerApp") -> None:
        self.app = app

    def set_display_name(self, name: str) -> None:
        self.display_name = name

    def prepare_for_new_session(self) -> None:
        self.messages_display.text = ""
        self.message_input.text = ""
        self.update_status("Подключение...")

    def update_status(self, text: str) -> None:
        self.status_label.text = text

    def add_message(self, data: dict) -> None:
        msg_type = data.get("type")
        if msg_type == "history":
            for item in data.get("messages", []):
                self._append_message(item)
        else:
            self._append_message(data)

    def _append_message(self, payload: dict) -> None:
        msg_type = payload.get("type")
        timestamp = self._format_timestamp(payload.get("timestamp"))
        if msg_type == "message":
            sender = payload.get("sender", "Неизвестно")
            content = payload.get("content", "")
            prefix = "Вы" if sender == self.display_name else sender
            line = f"[{timestamp}] {prefix}: {content}"
        elif msg_type == "system":
            line = f"[{timestamp}] * {payload.get('content', '')}"
        elif msg_type == "error":
            line = f"[{timestamp}] ! Ошибка: {payload.get('message') or payload.get('content', '')}"
        else:
            line = f"[{timestamp}] {payload}"
        if self.messages_display.text:
            self.messages_display.text += "\n" + line
        else:
            self.messages_display.text = line
        Clock.schedule_once(self._scroll_to_bottom, 0)

    def _format_timestamp(self, raw: Optional[str]) -> str:
        if not raw:
            return datetime.now().strftime("%H:%M:%S")
        raw = raw.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(raw)
            return dt.astimezone().strftime("%H:%M:%S")
        except ValueError:
            return raw[:8]

    def _scroll_to_bottom(self, *_args: Any) -> None:
        # Move caret to the end which scrolls the TextInput to the bottom.
        lines = getattr(self.messages_display, "_lines", [])
        line_count = len(lines) if isinstance(lines, list) else 0
        self.messages_display.cursor = (0, max(line_count - 1, 0))

    def _on_disconnect(self, *_args: Any) -> None:
        if self.app:
            self.app.disconnect_and_return()

    def _on_send(self, *_args: Any) -> None:
        text = self.message_input.text.strip()
        if not text or not self.app:
            return
        success = self.app.send_message(text)
        if success:
            self.message_input.text = ""
        else:
            self.update_status("Нет соединения. Повторите попытку позже.")


class MessengerApp(App):
    title = "Phone ↔ PC Messenger"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.display_name: str = ""
        self.host: str = ""
        self.port: int = 8765
        self.network_client: Optional[NetworkClient] = None
        self.message_queue: Optional[queue.Queue] = None
        self.status_queue: Optional[queue.Queue] = None
        self.queue_event: Optional[Any] = None
        self.setup_screen: Optional[SetupScreen] = None
        self.chat_screen: Optional[ChatScreen] = None

    def build(self) -> ScreenManager:
        manager = ScreenManager()
        self.setup_screen = SetupScreen()
        self.chat_screen = ChatScreen()
        self.setup_screen.set_app(self)
        self.chat_screen.set_app(self)
        manager.add_widget(self.setup_screen)
        manager.add_widget(self.chat_screen)
        return manager

    def start_chat(self, display_name: str, host: str, port: int) -> None:
        self.display_name = display_name
        self.host = host
        self.port = port
        uri = f"ws://{host}:{port}"

        if self.network_client:
            self.network_client.stop()

        self.message_queue = queue.Queue()
        self.status_queue = queue.Queue()

        self.network_client = NetworkClient(uri, display_name, self.message_queue, self.status_queue)
        self.network_client.start()

        if self.chat_screen:
            self.chat_screen.set_display_name(display_name)
            self.chat_screen.prepare_for_new_session()

        if self.queue_event:
            self.queue_event.cancel()
        self.queue_event = Clock.schedule_interval(self._process_queues, 0.2)

        self.root.current = "chat"

    def _process_queues(self, _dt: float) -> None:
        if self.status_queue:
            while True:
                try:
                    status, info = self.status_queue.get_nowait()
                except queue.Empty:
                    break
                self._handle_status(status, info)
        if self.message_queue:
            while True:
                try:
                    data = self.message_queue.get_nowait()
                except queue.Empty:
                    break
                if self.chat_screen:
                    self.chat_screen.add_message(data)

    def _handle_status(self, status: str, info: Optional[str]) -> None:
        if not self.chat_screen:
            return
        if status == "connecting":
            self.chat_screen.update_status("Подключение...")
        elif status == "connected":
            self.chat_screen.update_status("Подключено")
        elif status == "disconnected":
            reason = (info or "Соединение потеряно.")
            self.chat_screen.update_status(f"Отключено: {reason}")
        elif status == "error":
            self.chat_screen.update_status(f"Ошибка: {info}")
        elif status == "stopped":
            self.chat_screen.update_status("Отключено")

    def send_message(self, content: str) -> bool:
        if not self.network_client:
            return False
        return self.network_client.send_message(content)

    def disconnect_and_return(self) -> None:
        self._stop_network()
        if self.root:
            self.root.current = "setup"

    def _stop_network(self) -> None:
        if self.queue_event:
            self.queue_event.cancel()
            self.queue_event = None
        if self.network_client:
            self.network_client.stop()
            self.network_client = None
        self.message_queue = None
        self.status_queue = None

    def on_stop(self) -> None:
        self._stop_network()


if __name__ == "__main__":
    MessengerApp().run()
