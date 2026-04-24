"""Shared validator for user-supplied JSON `metadata_` dictionaries.

Caps the serialized size and nesting depth to prevent a caller from using
the free-form metadata field as a vector for DoS (huge payload or deeply
nested structure that blows the recursion limit in downstream code).
"""

from __future__ import annotations

import json

METADATA_MAX_BYTES = 4 * 1024
METADATA_MAX_DEPTH = 4


def _depth(value: object) -> int:
    if isinstance(value, dict):
        return 1 + max((_depth(v) for v in value.values()), default=0)
    if isinstance(value, list):
        return 1 + max((_depth(v) for v in value), default=0)
    return 0


def validate_metadata(value: dict | None) -> dict | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError("metadata_ must be an object")
    try:
        encoded = json.dumps(value, separators=(",", ":"), ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("metadata_ must be JSON-serializable") from exc
    if len(encoded.encode("utf-8")) > METADATA_MAX_BYTES:
        raise ValueError(
            f"metadata_ exceeds the maximum size of {METADATA_MAX_BYTES} bytes"
        )
    if _depth(value) > METADATA_MAX_DEPTH:
        raise ValueError(
            f"metadata_ exceeds the maximum nesting depth of {METADATA_MAX_DEPTH}"
        )
    return value
