from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth import (
    create_access_token,
    verify_password,
)
from app.services.refresh_sessions import (
    exchange_refresh_token,
    issue_refresh_session,
    refresh_cookie_max_age_seconds,
    revoke_refresh_session_family,
)

router = APIRouter(prefix="/auth", tags=["auth"])

limiter = Limiter(key_func=get_remote_address)
COOKIE_SECURE = settings.app_base_url.startswith("https://")


def _request_ip(request: Request) -> str | None:
    # TODO: Honor trusted proxy headers (for example X-Forwarded-For) behind Caddy/load balancers.
    return request.client.host if request.client else None


def _request_user_agent(request: Request) -> str | None:
    return request.headers.get("user-agent")


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="strict",
        max_age=refresh_cookie_max_age_seconds(),
        path="/api/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key="refresh_token",
        path="/api/auth",
        secure=COOKIE_SECURE,
        httponly=True,
        samesite="strict",
    )


def _refresh_failure_response(detail: str) -> JSONResponse:
    response = JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": detail},
    )
    _clear_refresh_cookie(response)
    return response


@router.post("/login", response_model=TokenResponse)
@limiter.limit(settings.rate_limit_login)
async def login(request: Request, body: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )
    access_token = create_access_token(
        user.user_id,
        user.role,
        user.linked_client_id,
        token_version=user.token_version,
    )
    refresh_token = await issue_refresh_session(
        db,
        user_id=user.user_id,
        created_ip=_request_ip(request),
        created_user_agent=_request_user_agent(request),
    )
    _set_refresh_cookie(response, refresh_token)
    return TokenResponse(access_token=access_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(None),
):
    if not refresh_token:
        return _refresh_failure_response("Session expired. Please sign in again.")

    exchange_result = await exchange_refresh_token(
        db,
        raw_token=refresh_token,
        current_ip=_request_ip(request),
        current_user_agent=_request_user_agent(request),
    )
    if exchange_result.status != "success" or not exchange_result.user or not exchange_result.refresh_token:
        return _refresh_failure_response("Session expired. Please sign in again.")

    access_token = create_access_token(
        exchange_result.user.user_id,
        exchange_result.user.role,
        exchange_result.user.linked_client_id,
        token_version=exchange_result.user.token_version,
    )
    _set_refresh_cookie(response, exchange_result.refresh_token)
    return TokenResponse(access_token=access_token)


@router.post("/logout")
async def logout(
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(None),
):
    if refresh_token:
        await revoke_refresh_session_family(
            db,
            raw_token=refresh_token,
            reason="logout",
        )
    _clear_refresh_cookie(response)
    return {"detail": "Logged out"}
