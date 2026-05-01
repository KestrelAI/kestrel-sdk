from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    server_url: str = ""
    session_token: str = ""
    user_id: str = ""
    email: str = ""

    @property
    def is_logged_in(self) -> bool:
        return bool(self.server_url and self.session_token)


_CONFIG_DIR = Path.home() / ".kestrel"
_CONFIG_PATH = _CONFIG_DIR / "config.json"


def config_path() -> Path:
    return _CONFIG_PATH


def load_config() -> Config:
    if not _CONFIG_PATH.exists():
        return Config()
    raw = json.loads(_CONFIG_PATH.read_text())
    return Config(
        server_url=raw.get("server_url", ""),
        session_token=raw.get("session_token", ""),
        user_id=raw.get("user_id", ""),
        email=raw.get("email", ""),
    )


def save_config(cfg: Config) -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    _CONFIG_PATH.write_text(
        json.dumps(
            {
                "server_url": cfg.server_url,
                "session_token": cfg.session_token,
                "user_id": cfg.user_id,
                "email": cfg.email,
            },
            indent=2,
        )
    )
    os.chmod(_CONFIG_PATH, 0o600)
