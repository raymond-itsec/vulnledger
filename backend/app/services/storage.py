import io
import logging
from collections.abc import Iterator
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

from minio import Minio

from app.config import settings

logger = logging.getLogger(__name__)

EVIDENCE_BUCKET_NAME = settings.minio_evidence_bucket
REPORTS_BUCKET_NAME = settings.minio_reports_bucket

ALLOWED_CONTENT_TYPES = {
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/webp",
    "application/pdf",
    "text/plain",
    "text/markdown",
    "text/csv",
    "application/json",
    "application/zip",
}

MAX_FILE_SIZE = settings.attachment_max_file_size_mb * 1024 * 1024


def content_type_matches_magic(declared: str, prefix: bytes) -> bool:
    """Verify that the first bytes of an upload are consistent with the
    client-declared Content-Type. Rejects the common trick of renaming a
    binary to a text MIME type (or vice versa) to slip past allowlists.
    """
    if not prefix:
        # Empty files aren't useful evidence; reject.
        return False

    if declared == "image/png":
        return prefix.startswith(b"\x89PNG\r\n\x1a\n")
    if declared == "image/jpeg":
        return prefix.startswith(b"\xff\xd8\xff")
    if declared == "image/gif":
        return prefix.startswith(b"GIF87a") or prefix.startswith(b"GIF89a")
    if declared == "image/webp":
        return prefix.startswith(b"RIFF") and len(prefix) >= 12 and prefix[8:12] == b"WEBP"
    if declared == "application/pdf":
        return prefix.startswith(b"%PDF-")
    if declared == "application/zip":
        return (
            prefix.startswith(b"PK\x03\x04")
            or prefix.startswith(b"PK\x05\x06")
            or prefix.startswith(b"PK\x07\x08")
        )
    if declared in {"text/plain", "text/markdown", "text/csv", "application/json"}:
        # Text-family: reject anything containing NULs or that fails to decode as UTF-8.
        if b"\x00" in prefix:
            return False
        try:
            prefix.decode("utf-8")
        except UnicodeDecodeError:
            # Truncation mid-codepoint is allowed; other decode errors are not.
            try:
                prefix[:-3].decode("utf-8")
            except UnicodeDecodeError:
                return False
        return True

    return False


def get_minio_client() -> Minio:
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )


def ensure_buckets() -> None:
    client = get_minio_client()
    for bucket_name in (EVIDENCE_BUCKET_NAME, REPORTS_BUCKET_NAME):
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            logger.info("Created MinIO bucket: %s", bucket_name)


def _put_object(
    bucket_name: str,
    storage_key: str,
    content_type: str,
    data: bytes,
) -> str:
    client = get_minio_client()
    client.put_object(
        bucket_name,
        storage_key,
        io.BytesIO(data),
        length=len(data),
        content_type=content_type,
    )
    return storage_key


def _put_object_stream(
    bucket_name: str,
    storage_key: str,
    content_type: str,
    data_stream: BinaryIO,
    length: int,
) -> str:
    client = get_minio_client()
    client.put_object(
        bucket_name,
        storage_key,
        data_stream,
        length=length,
        content_type=content_type,
    )
    return storage_key


def upload_evidence_file(
    finding_id: str,
    file_name: str,
    content_type: str,
    data: bytes,
) -> str:
    unique_name = f"{uuid4().hex}-{file_name}"
    storage_key = f"findings/{finding_id}/{unique_name}"
    return _put_object(EVIDENCE_BUCKET_NAME, storage_key, content_type, data)


def upload_evidence_file_stream(
    finding_id: str,
    file_name: str,
    content_type: str,
    data_stream: BinaryIO,
    length: int,
) -> str:
    unique_name = f"{uuid4().hex}-{file_name}"
    storage_key = f"findings/{finding_id}/{unique_name}"
    return _put_object_stream(
        EVIDENCE_BUCKET_NAME,
        storage_key,
        content_type,
        data_stream,
        length,
    )


def upload_report_file(
    session_id: str,
    file_name: str,
    content_type: str,
    data: bytes,
) -> str:
    suffix = Path(file_name).suffix or ""
    storage_key = f"sessions/{session_id}/{uuid4().hex}{suffix}"
    return _put_object(REPORTS_BUCKET_NAME, storage_key, content_type, data)


def _download_file(bucket_name: str, storage_key: str) -> tuple[bytes, str]:
    client = get_minio_client()
    response = client.get_object(bucket_name, storage_key)
    try:
        data = response.read()
    finally:
        response.close()
        response.release_conn()
    content_type = response.headers.get("Content-Type", "application/octet-stream")
    return data, content_type


def download_evidence_file(storage_key: str) -> tuple[bytes, str]:
    return _download_file(EVIDENCE_BUCKET_NAME, storage_key)


def stream_report_file(
    storage_key: str,
    chunk_size: int = 64 * 1024,
) -> tuple[Iterator[bytes], str]:
    client = get_minio_client()
    response = client.get_object(REPORTS_BUCKET_NAME, storage_key)
    content_type = response.headers.get("Content-Type", "application/octet-stream")

    def iterator() -> Iterator[bytes]:
        try:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                yield chunk
        finally:
            response.close()
            response.release_conn()

    return iterator(), content_type


def stream_evidence_file(
    storage_key: str,
    chunk_size: int = 64 * 1024,
) -> tuple[Iterator[bytes], str]:
    client = get_minio_client()
    response = client.get_object(EVIDENCE_BUCKET_NAME, storage_key)
    content_type = response.headers.get("Content-Type", "application/octet-stream")

    def iterator() -> Iterator[bytes]:
        try:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                yield chunk
        finally:
            response.close()
            response.release_conn()

    return iterator(), content_type


def delete_evidence_file(storage_key: str) -> None:
    client = get_minio_client()
    client.remove_object(EVIDENCE_BUCKET_NAME, storage_key)


def delete_report_file(storage_key: str) -> None:
    client = get_minio_client()
    client.remove_object(REPORTS_BUCKET_NAME, storage_key)
