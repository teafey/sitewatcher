from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

import httpx

from src.config import settings
from src.notify.base import BaseNotifier

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}"


class TelegramNotifier(BaseNotifier):
    def __init__(self) -> None:
        self._base_url = TELEGRAM_API.format(token=settings.telegram_bot_token)
        self._chat_id = settings.telegram_chat_id
        self._last_send_time: float = 0

    async def _rate_limit(self) -> None:
        """Ensure at least 1 second between messages."""
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_send_time
        if elapsed < 1.0:
            await asyncio.sleep(1.0 - elapsed)
        self._last_send_time = asyncio.get_event_loop().time()

    async def send_change_alert(
        self,
        page: dict[str, Any],
        snapshot: dict[str, Any],
    ) -> bool:
        try:
            await self._rate_limit()

            name = page.get("name") or page["url"]
            url = page["url"]
            diff_percent = snapshot.get("diff_percent", 0) or 0
            captured_at = snapshot.get("captured_at", "")

            # Determine change type
            has_pixel = diff_percent > 0
            has_text = bool(snapshot.get("text_diff"))
            if has_pixel and has_text:
                change_type = "визуальный + текстовый"
            elif has_pixel:
                change_type = "визуальный"
            else:
                change_type = "текстовый"

            text = (
                f"\U0001f534 *{_escape_md(name)}*\n"
                f"URL: {_escape_md(url)}\n"
                f"Diff: {diff_percent:.2f}%\n"
                f"Тип: {change_type}\n"
                f"Время: {_escape_md(captured_at)}"
            )

            diff_image_path = snapshot.get("diff_image_path")
            if diff_image_path and Path(diff_image_path).exists():
                return await self._send_photo(diff_image_path, text)
            else:
                return await self._send_message(text)

        except Exception as exc:
            logger.error("Telegram notification failed: %s", exc)
            return False

    async def _send_photo(self, photo_path: str, caption: str) -> bool:
        path = Path(photo_path)
        # Compress if > 10MB
        file_size = path.stat().st_size
        if file_size > 10 * 1024 * 1024:
            from PIL import Image
            img = Image.open(path)
            compressed_path = path.parent / "diff_compressed.jpg"
            img.save(str(compressed_path), "JPEG", quality=70)
            path = compressed_path

        async with httpx.AsyncClient(timeout=30.0) as client:
            with open(path, "rb") as f:
                resp = await client.post(
                    f"{self._base_url}/sendPhoto",
                    data={
                        "chat_id": self._chat_id,
                        "caption": caption,
                        "parse_mode": "Markdown",
                    },
                    files={"photo": f},
                )
            resp.raise_for_status()
            logger.info("Telegram photo sent successfully")
            return True

    async def _send_message(self, text: str) -> bool:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self._base_url}/sendMessage",
                json={
                    "chat_id": self._chat_id,
                    "text": text,
                    "parse_mode": "Markdown",
                },
            )
            resp.raise_for_status()
            logger.info("Telegram message sent successfully")
            return True


def _escape_md(text: str) -> str:
    """Escape special Markdown characters."""
    for char in ("_", "*", "[", "]", "(", ")", "~", "`", ">", "#", "+", "-", "=", "|", "{", "}", ".", "!"):
        text = text.replace(char, f"\\{char}")
    return text
