import math
from uuid import UUID

from fastapi import Cookie, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.auth import decode_token

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(credentials.credentials)
    user_id = payload.get("sub")
    token_type = payload.get("type")
    token_version = payload.get("ver", 0)
    if not isinstance(token_version, int):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    if not user_id or token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    result = await db.execute(select(User).where(User.user_id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    if token_version != user.token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has been revoked",
        )
    return user


def require_role(*roles: str):
    async def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' is not authorized for this action",
            )
        return user
    return checker


def get_client_scope(user: User) -> UUID | None:
    """Return the client_id to filter by, or None if unrestricted."""
    if user.role == "client_user":
        return user.linked_client_id
    return None


def ensure_client_access(user: User, client_id: UUID | None) -> None:
    """Raise 403 if the user is scoped to a client and ``client_id`` does not match.

    Unscoped users (admins, reviewers) always pass. Scoped users (client_user)
    must match their linked client; a missing (None) client_id is also refused
    to avoid silently passing on broken object chains.
    """
    scope = get_client_scope(user)
    if scope is None:
        return
    if client_id is None or client_id != scope:
        raise HTTPException(status_code=403, detail="Access denied")


async def paginate(
    db: AsyncSession,
    query: Select,
    page: int = 1,
    per_page: int = 25,
    unique: bool = False,
) -> dict:
    """Execute a query with pagination and return items + metadata."""
    # Count total
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    pages = math.ceil(total / per_page) if per_page > 0 else 0

    # Fetch page
    paginated = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(paginated)
    if unique:
        items = result.unique().scalars().all()
    else:
        items = result.scalars().all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages,
    }
