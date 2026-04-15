import io
import logging
from uuid import uuid4

from minio import Minio
from minio.error import S3Error

from app.config import settings

logger = logging.getLogger(__name__)

BUCKET_NAME = "finding-attachments"

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

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB


def get_minio_client() -> Minio:
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )


def ensure_bucket() -> None:
    client = get_minio_client()
    if not client.bucket_exists(BUCKET_NAME):
        client.make_bucket(BUCKET_NAME)
        logger.info("Created MinIO bucket: %s", BUCKET_NAME)


def upload_file(
    finding_id: str,
    file_name: str,
    content_type: str,
    data: bytes,
) -> str:
    """Upload a file to MinIO and return the storage key."""
    client = get_minio_client()
    unique_name = f"{uuid4().hex}-{file_name}"
    storage_key = f"findings/{finding_id}/{unique_name}"
    client.put_object(
        BUCKET_NAME,
        storage_key,
        io.BytesIO(data),
        length=len(data),
        content_type=content_type,
    )
    return storage_key


def download_file(storage_key: str) -> tuple[bytes, str]:
    """Download a file from MinIO. Returns (data, content_type)."""
    client = get_minio_client()
    response = client.get_object(BUCKET_NAME, storage_key)
    try:
        data = response.read()
    finally:
        response.close()
        response.release_conn()
    content_type = response.headers.get("Content-Type", "application/octet-stream")
    return data, content_type


def delete_file(storage_key: str) -> None:
    """Delete a file from MinIO."""
    client = get_minio_client()
    client.remove_object(BUCKET_NAME, storage_key)
