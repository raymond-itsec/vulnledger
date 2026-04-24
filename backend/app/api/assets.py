from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ensure_client_access, get_client_scope, get_current_user, paginate, require_role
from app.database import get_db
from app.models.reviewed_asset import ReviewedAsset
from app.models.user import User
from app.schemas.asset import AssetCreate, AssetResponse, AssetUpdate
from app.schemas.pagination import PaginatedResponse
from app.services.taxonomy import TaxonomyError, require_taxonomy_value

router = APIRouter(prefix="/assets", tags=["assets"])

admin_or_reviewer = require_role("admin", "reviewer")


@router.get("", response_model=PaginatedResponse[AssetResponse])
async def list_assets(
    client_id: UUID | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(ReviewedAsset).order_by(ReviewedAsset.asset_name)
    scope = get_client_scope(user)
    if scope:
        query = query.where(ReviewedAsset.client_id == scope)
    elif client_id:
        query = query.where(ReviewedAsset.client_id == client_id)
    return await paginate(db, query, page, per_page)


@router.post("", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(
    body: AssetCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_or_reviewer),
):
    try:
        await require_taxonomy_value(db, "asset_type", body.asset_type)
    except TaxonomyError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    asset = ReviewedAsset(
        client_id=body.client_id,
        asset_name=body.asset_name,
        asset_type=body.asset_type,
        description=body.description,
        metadata_=body.metadata_ or {},
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return asset


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ReviewedAsset).where(ReviewedAsset.asset_id == asset_id)
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    ensure_client_access(user, asset.client_id)
    return asset


@router.patch("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: UUID,
    body: AssetUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_or_reviewer),
):
    result = await db.execute(
        select(ReviewedAsset).where(ReviewedAsset.asset_id == asset_id)
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    update_data = body.model_dump(exclude_unset=True)
    if "asset_type" in update_data:
        try:
            await require_taxonomy_value(db, "asset_type", update_data["asset_type"])
        except TaxonomyError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    if "client_id" in update_data:
        asset.client_id = update_data["client_id"]
    if "asset_name" in update_data:
        asset.asset_name = update_data["asset_name"]
    if "asset_type" in update_data:
        asset.asset_type = update_data["asset_type"]
    if "description" in update_data:
        asset.description = update_data["description"]
    if "metadata_" in update_data:
        asset.metadata_ = update_data["metadata_"]
    await db.commit()
    await db.refresh(asset)
    return asset
