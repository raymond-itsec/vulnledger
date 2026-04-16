from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.deps import get_client_scope, get_current_user, paginate, require_role
from app.database import get_db
from app.models.review_session import ReviewSession
from app.models.reviewed_asset import ReviewedAsset
from app.models.user import User
from app.schemas.pagination import PaginatedResponse
from app.schemas.session import SessionCreate, SessionResponse, SessionUpdate
from app.services.taxonomy import TaxonomyError, require_taxonomy_value

router = APIRouter(prefix="/sessions", tags=["sessions"])

admin_or_reviewer = require_role("admin", "reviewer")


async def _validate_session_relations(
    db: AsyncSession,
    asset_id: UUID,
    reviewer_id: UUID,
) -> None:
    asset_result = await db.execute(
        select(ReviewedAsset.asset_id).where(ReviewedAsset.asset_id == asset_id)
    )
    if asset_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Asset not found")

    reviewer_result = await db.execute(
        select(User).where(User.user_id == reviewer_id)
    )
    reviewer = reviewer_result.scalar_one_or_none()
    if not reviewer or not reviewer.is_active:
        raise HTTPException(status_code=422, detail="Reviewer not found or inactive")
    if reviewer.role not in {"admin", "reviewer"}:
        raise HTTPException(status_code=422, detail="Reviewer must have admin or reviewer role")


def _to_response(session: ReviewSession) -> SessionResponse:
    return SessionResponse(
        session_id=session.session_id,
        asset_id=session.asset_id,
        review_name=session.review_name,
        review_date=session.review_date,
        reviewer_id=session.reviewer_id,
        reviewer_name=session.reviewer.full_name if session.reviewer else None,
        status=session.status,
        notes=session.notes,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.get("", response_model=PaginatedResponse[SessionResponse])
async def list_sessions(
    asset_id: UUID | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = (
        select(ReviewSession)
        .options(joinedload(ReviewSession.reviewer), joinedload(ReviewSession.asset))
        .order_by(ReviewSession.review_date.desc())
    )
    scope = get_client_scope(user)
    if scope:
        query = query.join(ReviewedAsset).where(ReviewedAsset.client_id == scope)
    if asset_id:
        query = query.where(ReviewSession.asset_id == asset_id)
    result = await paginate(db, query, page, per_page, unique=True)
    result["items"] = [_to_response(s) for s in result["items"]]
    return result


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    body: SessionCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_or_reviewer),
):
    try:
        await require_taxonomy_value(db, "session_status", body.status)
    except TaxonomyError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await _validate_session_relations(db, body.asset_id, body.reviewer_id)
    session = ReviewSession(
        asset_id=body.asset_id,
        review_name=body.review_name,
        review_date=body.review_date,
        reviewer_id=body.reviewer_id,
        status=body.status,
        notes=body.notes,
    )
    db.add(session)
    await db.commit()
    result = await db.execute(
        select(ReviewSession)
        .options(joinedload(ReviewSession.reviewer))
        .where(ReviewSession.session_id == session.session_id)
    )
    session = result.unique().scalar_one()
    return _to_response(session)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ReviewSession)
        .options(joinedload(ReviewSession.reviewer), joinedload(ReviewSession.asset))
        .where(ReviewSession.session_id == session_id)
    )
    session = result.unique().scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    scope = get_client_scope(user)
    if scope and session.asset.client_id != scope:
        raise HTTPException(status_code=403, detail="Access denied")
    return _to_response(session)


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: UUID,
    body: SessionUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_or_reviewer),
):
    result = await db.execute(
        select(ReviewSession)
        .options(joinedload(ReviewSession.reviewer))
        .where(ReviewSession.session_id == session_id)
    )
    session = result.unique().scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    update_data = body.model_dump(exclude_unset=True)
    if "status" in update_data:
        try:
            await require_taxonomy_value(db, "session_status", update_data["status"])
        except TaxonomyError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    reviewer_id = update_data.get("reviewer_id", session.reviewer_id)
    asset_id = update_data.get("asset_id", session.asset_id)
    if "reviewer_id" in update_data:
        await _validate_session_relations(db, asset_id, reviewer_id)
    for field, value in update_data.items():
        setattr(session, field, value)
    await db.commit()
    result = await db.execute(
        select(ReviewSession)
        .options(joinedload(ReviewSession.reviewer))
        .where(ReviewSession.session_id == session.session_id)
    )
    session = result.unique().scalar_one()
    return _to_response(session)
