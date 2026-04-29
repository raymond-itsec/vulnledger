"""ClamAV virus scanning for file attachments."""

import io
import logging
from typing import BinaryIO

import clamd

from app.config import settings

logger = logging.getLogger(__name__)


def _get_scanner() -> clamd.ClamdNetworkSocket | None:
    if not settings.clamav_host:
        return None
    try:
        scanner = clamd.ClamdNetworkSocket(
            host=settings.clamav_host,
            port=settings.clamav_port,
            timeout=30,
        )
        scanner.ping()
        return scanner
    except Exception:
        logger.warning("ClamAV not reachable at %s:%s", settings.clamav_host, settings.clamav_port)
        return None


def probe_scanner() -> tuple[str, str]:
    """Return scanner health state for diagnostics without raising exceptions.

    States:
        - "disabled": scanner is not configured
        - "ok": scanner reachable and responding
        - "down": scanner configured but unreachable
    """
    if not settings.clamav_host:
        return "disabled", "not configured"

    try:
        scanner = clamd.ClamdNetworkSocket(
            host=settings.clamav_host,
            port=settings.clamav_port,
            timeout=30,
        )
        scanner.ping()
        return "ok", "reachable"
    except Exception:
        return "down", "unreachable"


def scan_file(data: bytes, filename: str) -> tuple[bool, str]:
    return scan_file_stream(io.BytesIO(data), filename)


def scan_file_stream(file_stream: BinaryIO, filename: str) -> tuple[bool, str]:
    """Scan file data for viruses.

    Returns:
        (is_clean, message) -- False for infected uploads and any scanner
        misconfiguration or unavailability.
    """
    if not settings.clamav_host:
        return False, "Virus scanner is disabled. File uploads require ClamAV to be configured."

    scanner = _get_scanner()
    if scanner is None:
        return False, "Virus scanner is not available. File uploads are blocked until ClamAV is reachable."

    try:
        file_stream.seek(0)
        result = scanner.instream(file_stream)
        # result looks like: {'stream': ('OK', None)} or {'stream': ('FOUND', 'Eicar-Test-Signature')}
        status, reason = result.get("stream", ("ERROR", "Unknown"))
        if status == "OK":
            return True, "Clean"
        elif status == "FOUND":
            logger.warning("Virus detected in %s: %s", filename, reason)
            return False, f"Virus detected: {reason}"
        else:
            logger.error("ClamAV scan error for %s: %s %s", filename, status, reason)
            return False, f"Scan inconclusive: {status}"
    except Exception:
        logger.exception("ClamAV scan failed for %s", filename)
        return False, "Virus scanner error. File uploads are blocked until ClamAV is healthy."
