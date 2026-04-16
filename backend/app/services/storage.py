import io
import logging
from collections.abc import Iterator
from pathlib import Path
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


def upload_evidence_file(
    finding_id: str,
    file_name: str,
    content_type: str,
    data: bytes,
) -> str:
    unique_name = f"{uuid4().hex}-{file_name}"
    storage_key = f"findings/{finding_id}/{unique_name}"
    return _put_object(EVIDENCE_BUCKET_NAME, storage_key, content_type, data)


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
