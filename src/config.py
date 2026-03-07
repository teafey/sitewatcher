from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    # Supabase
    supabase_url: str = field(default_factory=lambda: os.getenv("SUPABASE_URL", ""))
    supabase_key: str = field(default_factory=lambda: os.getenv("SUPABASE_KEY", ""))

    # Telegram
    telegram_bot_token: str = field(default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", ""))
    telegram_chat_id: str = field(default_factory=lambda: os.getenv("TELEGRAM_CHAT_ID", ""))

    # Bitrix24
    bitrix_webhook_url: str = field(default_factory=lambda: os.getenv("BITRIX_WEBHOOK_URL", ""))

    # API
    api_key: str = field(default_factory=lambda: os.getenv("API_KEY", ""))

    # Dashboard
    dashboard_url: str = field(default_factory=lambda: os.getenv("DASHBOARD_URL", "http://localhost:8000"))

    # Scheduling
    check_interval_hours: int = field(
        default_factory=lambda: int(os.getenv("CHECK_INTERVAL_HOURS", "24"))
    )

    # Data
    data_dir: Path = field(
        default_factory=lambda: Path(os.getenv("DATA_DIR", "./data"))
    )

    @property
    def telegram_enabled(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_chat_id)

    @property
    def bitrix_enabled(self) -> bool:
        return bool(self.bitrix_webhook_url)


settings = Settings()
