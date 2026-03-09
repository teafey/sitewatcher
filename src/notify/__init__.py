from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.config import settings

if TYPE_CHECKING:
    from src.notify.base import BaseNotifier

logger = logging.getLogger(__name__)


def get_notifiers() -> list[BaseNotifier]:
    notifiers: list[BaseNotifier] = []

    if settings.telegram_enabled:
        from src.notify.telegram import TelegramNotifier
        notifiers.append(TelegramNotifier())
        logger.info("Telegram notifier enabled")

    if settings.bitrix_enabled:
        from src.notify.bitrix import BitrixNotifier
        notifiers.append(BitrixNotifier())
        logger.info("Bitrix24 notifier enabled")

    if not notifiers:
        logger.warning("No notification channels configured")

    return notifiers
