"""Minimal in-memory TTL cache.

Used as the last fallback tier: if every live request path fails, we'd
rather serve a slightly-stale cached response than a 502. Not safe for
multi-process deployment as-is -- swap the dict for Redis if you scale
past a single worker.
"""

import time
from typing import Any, Optional, Tuple


class TTLCache:
    def __init__(self) -> None:
        self._store: dict[str, Tuple[float, Any]] = {}

    def get_fresh(self, key: str, ttl: float) -> Optional[Any]:
        entry = self._store.get(key)
        if not entry:
            return None
        ts, value = entry
        return value if (time.monotonic() - ts) <= ttl else None

    def get_stale(self, key: str, max_age: float) -> Optional[Any]:
        entry = self._store.get(key)
        if not entry:
            return None
        ts, value = entry
        return value if (time.monotonic() - ts) <= max_age else None

    def set(self, key: str, value: Any) -> None:
        self._store[key] = (time.monotonic(), value)
