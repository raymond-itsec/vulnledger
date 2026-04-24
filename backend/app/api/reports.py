import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.deps import get_client_scope, get_current_user
from app.database import get_db
from app.models.finding import Finding
from app.models.report_export import ReportExport
from app.models.review_session import ReviewSession
from app.models.reviewed_asset import ReviewedAsset
from app.models.user import User
from app.services.html_safety import content_disposition_attachment
from app.services.reports import (
    ReportLimitError,
    generate_csv,
    generate_json,
    generate_pdf,
)
from app.services.storage import stream_report_file, upload_report_file
from app.services.taxonomy import get_current_taxonomy
from app.schemas.report_export import ReportExportResponse

router = APIRouter(prefix="/reports", tags=["reports"])
logger = logging.getLogger(__name__)


async def _get_session_with_findings(
    session_id: UUID, db: AsyncSession, user: User
) -> tuple[ReviewSession, list[Finding]]:
    result = await db.execute(
        select(ReviewSession)
        .options(
            joinedload(ReviewSession.reviewer),
            joinedload(ReviewSession.asset),
        )
        .where(ReviewSession.session_id == session_id)
    )
    session = result.unique().scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    scope = get_client_scope(user)
    if scope and session.asset and session.asset.client_id != scope:
        raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(
        select(Finding)
        .where(Finding.session_id == session_id)
        .order_by(Finding.created_at)
    )
    findings = list(result.scalars().all())
    return session, findings


def _safe_file_name(review_name: str, report_format: str) -> str:
    safe_name = review_name.replace(" ", "_")[:50]
    return f"report_{safe_name}.{report_format}"


def _to_export_response(export: ReportExport) -> ReportExportResponse:
    return ReportExportResponse(
        export_id=export.export_id,
        session_id=export.session_id,
        file_name=export.file_name,
        report_format=export.report_format,
        content_type=export.content_type,
        size_bytes=export.size_bytes,
        created_by=export.created_by,
        created_by_name=export.creator.full_name if export.creator else None,
        exported_at=export.exported_at,
    )


async def _record_export(
    db: AsyncSession,
    session: ReviewSession,
    user: User,
    taxonomy_version_id,
    report_format: str,
    content_type: str,
    data: bytes,
) -> ReportExport:
    file_name = _safe_file_name(session.review_name, report_format)
    storage_key = upload_report_file(
        str(session.session_id),
        file_name,
        content_type,
        data,
    )
    export = ReportExport(
        session_id=session.session_id,
        file_name=file_name,
        storage_key=storage_key,
        report_format=report_format,
        content_type=content_type,
        size_bytes=len(data),
        created_by=user.user_id,
        taxonomy_version_id=taxonomy_version_id,
    )
    db.add(export)
    await db.commit()
    await db.refresh(export)
    return export


@router.get("/sessions/{session_id}/exports", response_model=list[ReportExportResponse])
async def list_exports(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session, _ = await _get_session_with_findings(session_id, db, user)
    result = await db.execute(
        select(ReportExport)
        .options(joinedload(ReportExport.creator))
        .where(ReportExport.session_id == session.session_id)
        .order_by(ReportExport.exported_at.desc())
    )
    exports = result.unique().scalars().all()
    return [_to_export_response(export) for export in exports]


@router.get("/exports/{export_id}/download")
async def download_export(
    export_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ReportExport)
        .options(joinedload(ReportExport.session).joinedload(ReviewSession.asset))
        .where(ReportExport.export_id == export_id)
    )
    export = result.unique().scalar_one_or_none()
    if not export:
        raise HTTPException(status_code=404, detail="Export not found")

    scope = get_client_scope(user)
    if scope and (
        not export.session
        or not export.session.asset
        or export.session.asset.client_id != scope
    ):
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        file_iterator, content_type = stream_report_file(export.storage_key)
    except Exception as e:
        logger.exception("Could not stream stored report export %s", export_id)
        raise HTTPException(status_code=502, detail="Could not download the stored report") from e

    return StreamingResponse(
        file_iterator,
        media_type=content_type,
        headers={"Content-Disposition": content_disposition_attachment(export.file_name)},
    )


@router.get("/sessions/{session_id}/pdf")
async def export_pdf(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session, findings = await _get_session_with_findings(session_id, db, user)
    try:
        taxonomy = await get_current_taxonomy(db)
        pdf_bytes = generate_pdf(session, findings, taxonomy)
        export = await _record_export(
            db,
            session,
            user,
            taxonomy.version.taxonomy_version_id,
            "pdf",
            "application/pdf",
            pdf_bytes,
        )
    except ReportLimitError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except Exception as e:
        logger.exception("Could not generate or store PDF report for session %s", session_id)
        raise HTTPException(status_code=502, detail="Could not generate the PDF report") from e
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": content_disposition_attachment(export.file_name)},
    )


@router.get("/sessions/{session_id}/csv")
async def export_csv(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session, findings = await _get_session_with_findings(session_id, db, user)
    try:
        taxonomy = await get_current_taxonomy(db)
        csv_bytes = generate_csv(session, findings, taxonomy)
        export = await _record_export(
            db,
            session,
            user,
            taxonomy.version.taxonomy_version_id,
            "csv",
            "text/csv",
            csv_bytes,
        )
    except ReportLimitError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except Exception as e:
        logger.exception("Could not generate or store CSV report for session %s", session_id)
        raise HTTPException(status_code=502, detail="Could not generate the CSV report") from e
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": content_disposition_attachment(export.file_name)},
    )


@router.get("/sessions/{session_id}/json")
async def export_json(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session, findings = await _get_session_with_findings(session_id, db, user)
    try:
        taxonomy = await get_current_taxonomy(db)
        json_bytes = generate_json(session, findings, taxonomy)
        export = await _record_export(
            db,
            session,
            user,
            taxonomy.version.taxonomy_version_id,
            "json",
            "application/json",
            json_bytes,
        )
    except ReportLimitError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except Exception as e:
        logger.exception("Could not generate or store JSON report for session %s", session_id)
        raise HTTPException(status_code=502, detail="Could not generate the JSON report") from e
    return Response(
        content=json_bytes,
        media_type="application/json",
        headers={"Content-Disposition": content_disposition_attachment(export.file_name)},
    )
