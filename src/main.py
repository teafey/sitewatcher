from __future__ import annotations

import argparse
import asyncio
import json
import logging
import signal
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0]:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data, ensure_ascii=False)


def setup_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logging.root.handlers = [handler]
    logging.root.setLevel(logging.INFO)


shutdown_event = asyncio.Event()


def handle_signal(sig: int, frame: object) -> None:
    logging.info("Received signal %s, initiating graceful shutdown...", sig)
    shutdown_event.set()


async def main() -> None:
    setup_logging()
    logger = logging.getLogger("sitewatcher")

    parser = argparse.ArgumentParser(description="SiteWatcher — Visual web page monitor")
    parser.add_argument("--check-all", action="store_true", help="Check all active pages")
    parser.add_argument("--check-page", type=str, help="Check a specific page by ID")
    args = parser.parse_args()

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    from src.pipeline import run_check_cycle, check_single_page

    if args.check_all:
        logger.info("Starting full check cycle")
        results = await run_check_cycle()
        logger.info("Cycle results: %s", json.dumps(results))

    elif args.check_page:
        logger.info("Checking page: %s", args.check_page)
        result = await check_single_page(args.check_page)
        logger.info("Page result: %s", json.dumps(result))

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
