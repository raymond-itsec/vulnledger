import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.deps import get_client_scope, get_current_user, paginate, require_role
from app.database import get_db
from app.models.finding import Finding
from app.models.finding_history import FindingHistory
from app.models.review_session import ReviewSession
from app.models.reviewed_asset import ReviewedAsset
from app.models.user import User
from app.services.email import notify_finding_status_changed, notify_new_finding
from app.schemas.finding import FindingCreate, FindingHistoryResponse, FindingResponse, FindingUpdate
from app.schemas.pagination import PaginatedResponse
from app.services.taxonomy import TaxonomyError, get_current_taxonomy, require_taxonomy_value

router = APIRouter(prefix="/findings", tags=["findings"])
logger = logging.getLogger(__name__)

admin_or_reviewer = require_role("admin", "reviewer")

TRACKED_FIELDS = [
    "title", "description", "risk_level", "impact",
    "recommendation", "remediation_status", "references",
]


async def _check_finding_access(
    finding: Finding, user: User, db: AsyncSession
) -> None:
    scope = get_client_scope(user)
    if not scope:
        return
    result = await db.execute(
        select(ReviewSession)
        .options(joinedload(ReviewSession.asset))
        .where(ReviewSession.session_id == finding.session_id)
    )
    session = result.unique().scalar_one_or_none()
    if not session or session.asset.client_id != scope:
        raise HTTPException(status_code=403, detail="Access denied")


@router.get("", response_model=PaginatedResponse[FindingResponse])
async def list_findings(
    session_id: UUID | None = Query(None),
    risk_level: str | None = Query(None),
    remediation_status: str | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(Finding).order_by(Finding.created_at.desc())

    scope = get_client_scope(user)
    if scope:
        query = (
            query
            .join(ReviewSession)
            .join(ReviewedAsset)
            .where(ReviewedAsset.client_id == scope)
        )
    if session_id:
        query = query.where(Finding.session_id == session_id)
    if risk_level:
        query = query.where(Finding.risk_level == risk_level)
    if remediation_status:
        query = query.where(Finding.remediation_status == remediation_status)
    if search:
        pattern = f"%{search}%"
        query = query.where(
            Finding.title.ilike(pattern) | Finding.description.ilike(pattern)
        )

    return await paginate(db, query, page, per_page, unique=True)


@router.post("", response_model=FindingResponse, status_code=status.HTTP_201_CREATED)
async def create_finding(
    body: FindingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_or_reviewer),
):
    try:
        risk_entry = await require_taxonomy_value(db, "risk_level", body.risk_level)
        await require_taxonomy_value(db, "remediation_status", body.remediation_status)
    except TaxonomyError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    async with db.begin():
        finding = Finding(
            session_id=body.session_id,
            title=body.title,
            description=body.description,
            risk_level=body.risk_level,
            impact=body.impact,
            recommendation=body.recommendation,
            remediation_status=body.remediation_status,
            references=body.references,
        )
        db.add(finding)
    await db.refresh(finding)

    # Send email notification to session reviewer
    try:
        result = await db.execute(
            select(ReviewSession)
            .options(joinedload(ReviewSession.reviewer))
            .where(ReviewSession.session_id == body.session_id)
        )
        session = result.unique().scalar_one_or_none()
        if session and session.reviewer and session.reviewer.user_id != current_user.user_id:
            reviewer = session.reviewer
            if reviewer.email:
                notify_new_finding(
                    to_email=reviewer.email,
                    to_name=reviewer.full_name or reviewer.username,
                    finding_title=finding.title,
                    risk_level_label=risk_entry.label if risk_entry else finding.risk_level,
                    risk_color=(risk_entry.color or "#6b7280") if risk_entry else "#6b7280",
                    session_name=session.review_name,
                    finding_id=str(finding.finding_id),
                )
    except Exception:
        logger.warning(
            "New-finding notification failed for session %s",
            body.session_id,
            exc_info=True,
        )

    return finding


@router.get("/{finding_id}", response_model=FindingResponse)
async def get_finding(
    finding_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Finding).where(Finding.finding_id == finding_id))
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    await _check_finding_access(finding, user, db)
    return finding


@router.patch("/{finding_id}", response_model=FindingResponse)
async def update_finding(
    finding_id: UUID,
    body: FindingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_or_reviewer),
):
    result = await db.execute(select(Finding).where(Finding.finding_id == finding_id))
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    old_status = finding.remediation_status
    update_data = body.model_dump(exclude_unset=True)
    try:
        if "risk_level" in update_data:
            await require_taxonomy_value(db, "risk_level", update_data["risk_level"])
        if "remediation_status" in update_data:
            await require_taxonomy_value(
                db, "remediation_status", update_data["remediation_status"]
            )
    except TaxonomyError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    async with db.begin():
        # Track changes
        for field in TRACKED_FIELDS:
            if field not in update_data:
                continue
            old_val = getattr(finding, field)
            new_val = update_data[field]
            old_str = str(old_val) if old_val is not None else None
            new_str = str(new_val) if new_val is not None else None
            if old_str != new_str:
                db.add(FindingHistory(
                    finding_id=finding_id,
                    changed_by=current_user.user_id,
                    field_name=field,
                    old_value=old_str,
                    new_value=new_str,
                ))

        if "title" in update_data:
            finding.title = update_data["title"]
        if "description" in update_data:
            finding.description = update_data["description"]
        if "risk_level" in update_data:
            finding.risk_level = update_data["risk_level"]
        if "impact" in update_data:
            finding.impact = update_data["impact"]
        if "recommendation" in update_data:
            finding.recommendation = update_data["recommendation"]
        if "remediation_status" in update_data:
            finding.remediation_status = update_data["remediation_status"]
        if "references" in update_data:
            finding.references = update_data["references"]

    await db.refresh(finding)

    # Notify on status change
    if "remediation_status" in update_data and update_data["remediation_status"] != old_status:
        try:
            result = await db.execute(
                select(ReviewSession)
                .options(joinedload(ReviewSession.reviewer))
                .where(ReviewSession.session_id == finding.session_id)
            )
            session = result.unique().scalar_one_or_none()
            if session and session.reviewer and session.reviewer.user_id != current_user.user_id:
                reviewer = session.reviewer
                if reviewer.email:
                    taxonomy = await get_current_taxonomy(db)
                    notify_finding_status_changed(
                        to_email=reviewer.email,
                        to_name=reviewer.full_name or reviewer.username,
                        finding_title=finding.title,
                        old_status_label=taxonomy.label("remediation_status", old_status),
                        new_status_label=taxonomy.label(
                            "remediation_status", finding.remediation_status
                        ),
                        session_name=session.review_name,
                        finding_id=str(finding.finding_id),
                    )
        except Exception:
            logger.warning(
                "Status-change notification failed for finding %s",
                finding_id,
                exc_info=True,
            )

    return finding


@router.get("/{finding_id}/history", response_model=list[FindingHistoryResponse])
async def get_finding_history(
    finding_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Verify finding exists and user has access
    result = await db.execute(select(Finding).where(Finding.finding_id == finding_id))
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    await _check_finding_access(finding, user, db)

    result = await db.execute(
        select(FindingHistory)
        .options(joinedload(FindingHistory.user))
        .where(FindingHistory.finding_id == finding_id)
        .order_by(FindingHistory.changed_at.desc())
    )
    entries = result.unique().scalars().all()
    return [
        FindingHistoryResponse(
            history_id=e.history_id,
            finding_id=e.finding_id,
            changed_by=e.changed_by,
            changed_by_name=e.user.full_name if e.user else None,
            changed_at=e.changed_at,
            field_name=e.field_name,
            old_value=e.old_value,
            new_value=e.new_value,
        )
        for e in entries
    ]
