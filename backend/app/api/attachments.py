from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.deps import get_client_scope, get_current_user, require_role
from app.database import get_db
from app.models.finding import Finding
from app.models.finding_attachment import FindingAttachment
from app.models.review_session import ReviewSession
from app.models.user import User
from app.schemas.attachment import AttachmentResponse
from app.services.antivirus import scan_file
from app.services.storage import (
    ALLOWED_CONTENT_TYPES,
    MAX_FILE_SIZE,
    delete_file,
    download_file,
    upload_file,
)

router = APIRouter(tags=["attachments"])

admin_or_reviewer = require_role("admin", "reviewer")


async def _get_accessible_finding(
    finding_id: UUID,
    db: AsyncSession,
    user: User,
) -> Finding:
    result = await db.execute(
        select(Finding)
        .options(joinedload(Finding.session).joinedload(ReviewSession.asset))
        .where(Finding.finding_id == finding_id)
    )
    finding = result.unique().scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    scope = get_client_scope(user)
    if scope and (
        not finding.session
        or not finding.session.asset
        or finding.session.asset.client_id != scope
    ):
        raise HTTPException(status_code=403, detail="Access denied")

    return finding


@router.get(
    "/findings/{finding_id}/attachments",
    response_model=list[AttachmentResponse],
)
async def list_attachments(
    finding_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _get_accessible_finding(finding_id, db, user)
    result = await db.execute(
        select(FindingAttachment)
        .where(FindingAttachment.finding_id == finding_id)
        .order_by(FindingAttachment.uploaded_at.desc())
    )
    return result.scalars().all()


@router.post(
    "/findings/{finding_id}/attachments",
    response_model=AttachmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_attachment(
    finding_id: UUID,
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_or_reviewer),
):
    # Verify finding exists
    result = await db.execute(select(Finding).where(Finding.finding_id == finding_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Finding not found")

    # Validate content type
    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"File type '{content_type}' is not allowed. Allowed types: {sorted(ALLOWED_CONTENT_TYPES)}",
        )

    # Read and validate size
    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File size exceeds maximum of {MAX_FILE_SIZE // (1024*1024)} MB",
        )

    # Virus scan
    is_clean, scan_message = scan_file(data, file.filename or "unnamed")
    if not is_clean:
        raise HTTPException(
            status_code=422,
            detail=f"File rejected: {scan_message}",
        )

    # Upload to MinIO
    try:
        storage_key = upload_file(
            str(finding_id),
            file.filename or "unnamed",
            content_type,
            data,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Storage error: {e}")

    # Save metadata
    attachment = FindingAttachment(
        finding_id=finding_id,
        file_name=file.filename or "unnamed",
        storage_key=storage_key,
        content_type=content_type,
        size_bytes=len(data),
        uploaded_by=current_user.user_id,
    )
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)
    return attachment


@router.get("/attachments/{attachment_id}/download")
async def download_attachment(
    attachment_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(FindingAttachment)
        .options(
            joinedload(FindingAttachment.finding)
            .joinedload(Finding.session)
            .joinedload(ReviewSession.asset)
        )
        .where(FindingAttachment.attachment_id == attachment_id)
    )
    attachment = result.unique().scalar_one_or_none()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    scope = get_client_scope(user)
    if scope and (
        not attachment.finding
        or not attachment.finding.session
        or not attachment.finding.session.asset
        or attachment.finding.session.asset.client_id != scope
    ):
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        data, content_type = download_file(attachment.storage_key)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Storage error: {e}")

    return Response(
        content=data,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{attachment.file_name}"',
        },
    )


@router.delete(
    "/attachments/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_attachment(
    attachment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_or_reviewer),
):
    result = await db.execute(
        select(FindingAttachment).where(FindingAttachment.attachment_id == attachment_id)
    )
    attachment = result.scalar_one_or_none()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    try:
        delete_file(attachment.storage_key)
    except Exception:
        pass  # File may already be gone

    await db.delete(attachment)
    await db.commit()
