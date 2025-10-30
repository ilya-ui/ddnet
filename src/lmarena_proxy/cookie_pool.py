"""Simple cookie pool with round-robin semantics."""
from __future__ import annotations

import random
import threading
from typing import Iterable, List


class CookiePool:
    """Thread-safe pool for rotating arena-auth cookies."""

    def __init__(self, cookies: Iterable[str]):
        cleaned: List[str] = []
        seen = set()
        for cookie in cookies:
            cookie = cookie.strip()
            if not cookie or cookie in seen:
                continue
            seen.add(cookie)
            cleaned.append(cookie)
        if not cleaned:
            raise ValueError("CookiePool requires at least one cookie value.")
        self._cookies = cleaned
        self._lock = threading.Lock()
        self._index = random.randrange(len(self._cookies))

    def next(self) -> str:
        """Return the next cookie value, advancing the pointer."""
        with self._lock:
            value = self._cookies[self._index]
            self._index = (self._index + 1) % len(self._cookies)
            return value

    def ban(self, cookie: str) -> None:
        """Remove a cookie from rotation when it becomes invalid."""
        with self._lock:
            if cookie not in self._cookies:
                return
            self._cookies = [value for value in self._cookies if value != cookie]
            if not self._cookies:
                raise RuntimeError("All arena-auth cookies have been invalidated.")
            self._index %= len(self._cookies)

    def __len__(self) -> int:  # pragma: no cover - trivial
        with self._lock:
            return len(self._cookies)

    def snapshot(self) -> List[str]:
        """Return a copy of the currently available cookies."""
        with self._lock:
            return list(self._cookies)
