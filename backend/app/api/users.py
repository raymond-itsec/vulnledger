from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, paginate, require_role
from app.database import get_db
from app.models.user import User
from app.schemas.pagination import PaginatedResponse
from app.schemas.user import UserCreate, UserResponse, UserSelfUpdate, UserUpdate
from app.services.auth import hash_password

router = APIRouter(prefix="/users", tags=["users"])

admin_only = require_role("admin")


@router.get("", response_model=PaginatedResponse[UserResponse])
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_only),
):
    query = select(User).order_by(User.username)
    return await paginate(db, query, page, per_page)


@router.get("/reviewers", response_model=list[UserResponse])
async def list_reviewers(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin", "reviewer")),
):
    result = await db.execute(
        select(User)
        .where(User.is_active.is_(True), User.role.in_(("admin", "reviewer")))
        .order_by(User.full_name, User.username)
    )
    return result.scalars().all()


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_only),
):
    user = User(
        username=body.username,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        company_name=body.company_name,
        email=body.email,
        role=body.role,
        linked_client_id=body.linked_client_id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    body: UserSelfUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Email is already in use")

    await db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_only),
):
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_only),
):
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user
