from __future__ import annotations

import logging
from typing import Any

import httpx

from src.config import settings
from src.notify.base import BaseNotifier

logger = logging.getLogger(__name__)


class BitrixNotifier(BaseNotifier):
    def __init__(self) -> None:
        self._webhook_url = settings.bitrix_webhook_url.rstrip("/")

    async def send_change_alert(
        self,
        page: dict[str, Any],
        snapshot: dict[str, Any],
    ) -> bool:
        try:
            name = page.get("name") or page["url"]
            url = page["url"]
            diff_percent = snapshot.get("diff_percent", 0) or 0
            captured_at = snapshot.get("captured_at", "")
            snapshot_id = snapshot.get("id", "")

            dashboard_link = f"{settings.dashboard_url}/pages/{page['id']}"

            # Viewport info
            vw = snapshot.get("viewport_width")
            vh = snapshot.get("viewport_height")
            viewport_str = f"Viewport: {vw}x{vh}\n" if vw and vh else ""

            message = (
                f"[b]SiteWatcher: изменения обнаружены[/b]\n\n"
                f"Страница: [b]{name}[/b]\n"
                f"URL: {url}\n"
                f"Различия: {diff_percent:.2f}%\n"
                + viewport_str
                + f"Время: {captured_at}\n\n"
                f"[url={dashboard_link}]Открыть в дашборде[/url]"
            )

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self._webhook_url}/im.notify.personal.add.json",
                    json={"USER_ID": 1, "MESSAGE": message},
                )
                resp.raise_for_status()

            logger.info("Bitrix24 notification sent for page %s", name)
            return True

        except Exception as exc:
            logger.error("Bitrix24 notification failed: %s", exc)
            return False
