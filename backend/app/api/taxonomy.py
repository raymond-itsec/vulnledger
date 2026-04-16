from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_role
from app.database import get_db
from app.models.taxonomy import TaxonomyVersion
from app.models.user import User
from app.schemas.taxonomy import (
    TaxonomyEntryResponse,
    TaxonomyVersionActivate,
    TaxonomyVersionCreate,
    TaxonomyVersionResponse,
)
from app.services.taxonomy import (
    TaxonomyError,
    activate_taxonomy_version,
    create_taxonomy_version,
    get_current_taxonomy,
    get_taxonomy_version,
)

router = APIRouter(prefix="/taxonomy", tags=["taxonomy"])


def _serialize_bundle(bundle) -> TaxonomyVersionResponse:
    return TaxonomyVersionResponse(
        taxonomy_version_id=bundle.version.taxonomy_version_id,
        version_number=bundle.version.version_number,
        description=bundle.version.description,
        is_current=bundle.version.is_current,
        created_at=bundle.version.created_at,
        updated_at=bundle.version.updated_at,
        domains={
            domain: [TaxonomyEntryResponse.model_validate(entry) for entry in entries]
            for domain, entries in bundle.domains.items()
        },
    )


@router.get("/current", response_model=TaxonomyVersionResponse)
async def current_taxonomy(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    try:
        bundle = await get_current_taxonomy(db)
    except TaxonomyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _serialize_bundle(bundle)


@router.get("/versions", response_model=list[TaxonomyVersionResponse])
async def list_taxonomy_versions(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    result = await db.execute(
        select(TaxonomyVersion).order_by(TaxonomyVersion.version_number.desc())
    )
    versions = result.scalars().all()
    response: list[TaxonomyVersionResponse] = []
    for version in versions:
        bundle = await get_taxonomy_version(db, taxonomy_version_id=version.taxonomy_version_id)
        response.append(_serialize_bundle(bundle))
    return response


@router.post("/versions", response_model=TaxonomyVersionResponse)
async def create_version(
    body: TaxonomyVersionCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    try:
        bundle = await create_taxonomy_version(
            db,
            description=body.description,
            domains=body.domains,
            make_current=True,
        )
    except TaxonomyError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _serialize_bundle(bundle)


@router.post("/activate", response_model=TaxonomyVersionResponse)
async def activate_version(
    body: TaxonomyVersionActivate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    try:
        bundle = await activate_taxonomy_version(db, body.taxonomy_version_id)
    except TaxonomyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _serialize_bundle(bundle)
