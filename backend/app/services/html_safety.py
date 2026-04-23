from __future__ import annotations

import re
from html import escape

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
