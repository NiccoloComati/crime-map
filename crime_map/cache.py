from __future__ import annotations

import shutil
import time
from pathlib import Path

import requests

from .config import CACHE_DIR


def ensure_cache_dir() -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR


def cache_path(filename: str) -> Path:
    return ensure_cache_dir() / filename


def clear_cache_dir() -> None:
    if CACHE_DIR.exists():
        shutil.rmtree(CACHE_DIR, ignore_errors=True)


def is_fresh(path: Path, max_age_hours: float) -> bool:
    if not path.exists():
        return False
    age_seconds = time.time() - path.stat().st_mtime
    return age_seconds <= max_age_hours * 3600


def download_file(
    url: str,
    filename: str,
    *,
    max_age_hours: float = 24.0,
    force_refresh: bool = False,
    timeout: int = 120,
    headers: dict[str, str] | None = None,
) -> Path:
    destination = cache_path(filename)
    if not force_refresh and is_fresh(destination, max_age_hours):
        return destination

    response = requests.get(url, timeout=timeout, headers=headers)
    response.raise_for_status()
    destination.write_bytes(response.content)
    return destination
