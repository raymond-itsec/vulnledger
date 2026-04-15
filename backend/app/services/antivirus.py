"""ClamAV virus scanning for file attachments.

Scans files before they are stored in MinIO. Gracefully degrades
when ClamAV is not available (logs a warning, allows upload).
"""

import io
import logging

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


def scan_file(data: bytes, filename: str) -> tuple[bool, str]:
    """Scan file data for viruses.

    Returns:
        (is_clean, message) — True if clean or scanner unavailable, False if infected.
    """
    scanner = _get_scanner()
    if scanner is None:
        return True, "Scanner not available — skipped"

    try:
        result = scanner.instream(io.BytesIO(data))
        # result looks like: {'stream': ('OK', None)} or {'stream': ('FOUND', 'Eicar-Test-Signature')}
        status, reason = result.get("stream", ("ERROR", "Unknown"))
        if status == "OK":
            return True, "Clean"
        elif status == "FOUND":
            logger.warning("Virus detected in %s: %s", filename, reason)
            return False, f"Virus detected: {reason}"
        else:
            logger.error("ClamAV scan error for %s: %s %s", filename, status, reason)
            return True, f"Scan inconclusive: {status}"
    except Exception as e:
        logger.exception("ClamAV scan failed for %s", filename)
        return True, f"Scan error: {e}"
