from __future__ import annotations

import re
from html import escape
from urllib.parse import quote

import mistune

_COLOR_HEX_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
_MARKDOWN_RENDERER = mistune.create_markdown(escape=True)


def escape_html(value: object | None) -> str:
    if value is None:
        return ""
    return escape(str(value), quote=True)


def sanitize_markdown_to_html(markdown_text: str | None) -> str:
    if not markdown_text:
        return ""
    return _MARKDOWN_RENDERER(markdown_text)


def sanitize_hex_color(value: str | None, default: str = "#6b7280") -> str:
    if value and _COLOR_HEX_RE.fullmatch(value.strip()):
        return value.strip()
    return default


def sanitize_header_text(value: object | None) -> str:
    if value is None:
        return ""
    return str(value).replace("\r", " ").replace("\n", " ").strip()


_DISPOSITION_UNSAFE_RE = re.compile(r"[\x00-\x1f\x7f\"\\]")


def content_disposition_attachment(filename: str | None, fallback: str = "download") -> str:
    """Build a safe Content-Disposition: attachment header value.

    Strips control characters, quotes, and backslashes from the filename,
    and emits both an ASCII-safe filename= and an RFC 5987 filename*= for
    non-ASCII names. Prevents header injection (CRLF) and quote escape.
    """
    raw = (filename or "").replace("\r", "").replace("\n", "")
    sanitized = _DISPOSITION_UNSAFE_RE.sub("_", raw).strip().strip(".")
    if not sanitized:
        sanitized = fallback

    ascii_name = sanitized.encode("ascii", "replace").decode("ascii").replace("?", "_")
    encoded = quote(sanitized.encode("utf-8"), safe="")
    return f'attachment; filename="{ascii_name}"; filename*=UTF-8\'\'{encoded}'
