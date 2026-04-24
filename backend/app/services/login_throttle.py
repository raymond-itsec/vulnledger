"""Per-username sliding-window throttle for login attempts.

Complements the slowapi per-IP limiter on /login so a distributed botnet
cannot grind a single account by rotating source IPs below the per-IP cap.
In-process only; adequate for single-worker deployments or when the load
balancer pins a user to one worker.
"""

from __future__ import annotations

import asyncio
import re
import time
from collections import deque

from app.config import settings

_LIMIT_RE = re.compile(r"^\s*(\d+)\s*/\s*(second|minute|hour|day)s?\s*$", re.IGNORECASE)
_UNIT_SECONDS = {"second": 1, "minute": 60, "hour": 3600, "day": 86400}


def _parse_limit(raw: str) -> tuple[int, int]:
    match = _LIMIT_RE.match(raw or "")
    if not match:
        return 5, 60
    count = int(match.group(1))
    window = _UNIT_SECONDS[match.group(2).lower()]
    return max(1, count), window


_state: dict[str, deque[float]] = {}
_lock = asyncio.Lock()


async def check_login_allowed(username: str) -> bool:
    """Return True if another login attempt for `username` is permitted."""
    if not username:
        return True
    count, window = _parse_limit(settings.rate_limit_login)
    now = time.monotonic()
    cutoff = now - window
    key = username.strip().lower()
    async with _lock:
        hits = _state.get(key)
        if hits is None:
            hits = deque()
            _state[key] = hits
        while hits and hits[0] < cutoff:
            hits.popleft()
        if len(hits) >= count:
            return False
        hits.append(now)
        return True
