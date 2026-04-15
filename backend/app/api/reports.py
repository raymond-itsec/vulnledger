from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.deps import get_client_scope, get_current_user
from app.database import get_db
from app.models.finding import Finding
from app.models.review_session import ReviewSession
from app.models.reviewed_asset import ReviewedAsset
from app.models.user import User
from app.services.reports import generate_csv, generate_json, generate_pdf

router = APIRouter(prefix="/reports", tags=["reports"])


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


@router.get("/sessions/{session_id}/pdf")
async def export_pdf(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session, findings = await _get_session_with_findings(session_id, db, user)
    safe_name = session.review_name.replace(" ", "_")[:50]
    pdf_bytes = generate_pdf(session, findings)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="report_{safe_name}.pdf"'},
    )


@router.get("/sessions/{session_id}/csv")
async def export_csv(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session, findings = await _get_session_with_findings(session_id, db, user)
    safe_name = session.review_name.replace(" ", "_")[:50]
    csv_bytes = generate_csv(session, findings)
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="report_{safe_name}.csv"'},
    )


@router.get("/sessions/{session_id}/json")
async def export_json(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session, findings = await _get_session_with_findings(session_id, db, user)
    safe_name = session.review_name.replace(" ", "_")[:50]
    json_bytes = generate_json(session, findings)
    return Response(
        content=json_bytes,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="report_{safe_name}.json"'},
    )
