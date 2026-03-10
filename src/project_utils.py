from __future__ import annotations

from urllib.parse import urlparse


def extract_hostname(url: str) -> str:
    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL must include a valid hostname")
    return hostname.lower()


def normalize_base_url(url: str) -> str:
    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL must include a valid hostname")
    scheme = parsed.scheme or "https"
    return f"{scheme}://{hostname.lower()}"
