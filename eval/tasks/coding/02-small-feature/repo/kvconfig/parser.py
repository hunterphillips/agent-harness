"""Configuration parsing helpers."""

from __future__ import annotations

import re
from collections.abc import Iterable


def _normalize_key(key: str) -> str:
    normalized = re.sub(r"[-\s]+", "_", key.strip().lower())
    if not normalized:
        raise ValueError("configuration key cannot be empty")
    return normalized


def parse_lines(lines: Iterable[str]) -> dict[str, str]:
    """Parse NAME=VALUE lines, ignoring empty lines and comments."""
    parsed: dict[str, str] = {}
    for number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"line {number} has no '='")
        key, value = line.split("=", 1)
        parsed[_normalize_key(key)] = value.strip()
    return parsed
