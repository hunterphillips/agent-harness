"""Small, dependency-free slug generator."""

from __future__ import annotations

import re


def slugify(value: str) -> str:
    """Return a lowercase, hyphen-separated form of *value*."""
    normalized = value.strip().casefold()
    normalized = re.sub(r"[^\w\s-]", "", normalized)
    return re.sub(r"[-\s]+", "-", normalized).strip("-")
