"""Application configuration helpers."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import os

from dotenv import load_dotenv


def _load_dotenv() -> None:
    """Load variables from a local .env file if present."""
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path)


_load_dotenv()


def _split_env_list(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(slots=True)
class Settings:
    """Centralised environment configuration."""

    cf_clearance: str = field(default_factory=lambda: os.getenv("CF_CLEARANCE", ""))
    arena_cookies: List[str] = field(
        default_factory=lambda: _split_env_list(os.getenv("ARENA_AUTH_COOKIES"))
    )
    api_base_url: str = field(default_factory=lambda: os.getenv("ARENA_BASE_URL", "https://canary.lmarena.ai"))
    impersonate: str = field(default_factory=lambda: os.getenv("CURL_IMPERSONATE", "chrome137"))
    request_timeout: int = field(default_factory=lambda: int(os.getenv("ARENA_TIMEOUT_SECONDS", "120")))
    proxy_url: Optional[str] = field(default_factory=lambda: os.getenv("PROXY_URL") or None)
    auth_secret: Optional[str] = field(default_factory=lambda: os.getenv("API_AUTH_SECRET") or None)

    def __post_init__(self) -> None:
        if not self.cf_clearance:
            raise ValueError("CF_CLEARANCE environment variable is required.")
        if not self.arena_cookies:
            raise ValueError("ARENA_AUTH_COOKIES environment variable is required (comma separated).")
        self.api_base_url = self.api_base_url.rstrip("/")


_settings_cache: Optional[Settings] = None


def get_settings(refresh: bool = False) -> Settings:
    """Return cached settings, instantiating them if needed."""
    global _settings_cache
    if refresh:
        _settings_cache = None
    if _settings_cache is None:
        try:
            _settings_cache = Settings()
        except ValueError as exc:
            raise RuntimeError(
                "Configuration error: {}. Please configure CF_CLEARANCE and ARENA_AUTH_COOKIES (see README).".format(
                    exc
                )
            ) from exc
    return _settings_cache
