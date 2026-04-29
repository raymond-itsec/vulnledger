from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, paginate, require_role
from app.api.utils import apply_update_fields, taxonomy_http_error
from app.database import get_db
from app.models.finding_template import FindingTemplate
from app.models.user import User
from app.schemas.pagination import PaginatedResponse
from app.schemas.template import TemplateCreate, TemplateResponse, TemplateUpdate
from app.services.taxonomy import TaxonomyError, require_taxonomy_value

router = APIRouter(prefix="/templates", tags=["templates"])

admin_or_reviewer = require_role("admin", "reviewer")


@router.get("", response_model=PaginatedResponse[TemplateResponse])
async def list_templates(
    category: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = select(FindingTemplate).order_by(
        FindingTemplate.category, FindingTemplate.name
    )
    if category:
        query = query.where(FindingTemplate.category == category)
    return await paginate(db, query, page, per_page)


@router.post("", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    body: TemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_or_reviewer),
):
    if body.risk_level:
        try:
            await require_taxonomy_value(db, "risk_level", body.risk_level)
        except TaxonomyError as exc:
            raise taxonomy_http_error(exc) from exc
    template = FindingTemplate(
        stable_id=body.stable_id,
        name=body.name,
        category=body.category,
        is_builtin=False,
        title=body.title,
        description=body.description,
        risk_level=body.risk_level,
        impact=body.impact,
        recommendation=body.recommendation,
        references=body.references,
        created_by=current_user.user_id,
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(FindingTemplate).where(FindingTemplate.template_id == template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.patch("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: UUID,
    body: TemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_or_reviewer),
):
    result = await db.execute(
        select(FindingTemplate).where(FindingTemplate.template_id == template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    if template.is_builtin and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can edit built-in templates")
    if not template.is_builtin and template.created_by != current_user.user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to edit this template")
    update_data = body.model_dump(exclude_unset=True)
    if "risk_level" in update_data and update_data["risk_level"] is not None:
        try:
            await require_taxonomy_value(db, "risk_level", update_data["risk_level"])
        except TaxonomyError as exc:
            raise taxonomy_http_error(exc) from exc
    apply_update_fields(
        template,
        update_data,
        (
            "stable_id",
            "name",
            "category",
            "title",
            "description",
            "risk_level",
            "impact",
            "recommendation",
            "references",
        ),
    )
    await db.commit()
    await db.refresh(template)
    return template


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_or_reviewer),
):
    result = await db.execute(
        select(FindingTemplate).where(FindingTemplate.template_id == template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    if template.is_builtin:
        raise HTTPException(status_code=403, detail="Cannot delete built-in templates")
    if template.created_by != current_user.user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this template")
    await db.delete(template)
    await db.commit()
