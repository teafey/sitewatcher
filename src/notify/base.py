from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseNotifier(ABC):
    @abstractmethod
    async def send_change_alert(
        self,
        page: dict[str, Any],
        snapshot: dict[str, Any],
    ) -> bool:
        """Send a notification about detected changes. Returns True if sent successfully."""
        ...
