from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_active_user
from app.core.rate_limit import login_rate_limit, register_rate_limit
from app.db.session import get_db
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    MeResponse,
    MembershipResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth import AuthError, get_user_memberships, login_user, logout_user, refresh_tokens, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(register_rate_limit),
):
    try:
        _user, access_token, refresh_token = await register_user(data, db)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(login_rate_limit),
):
    try:
        _user, access_token, refresh_token = await login_user(data, db)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        access_token, refresh_token = await refresh_tokens(data.refresh_token, db)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(data: LogoutRequest, db: AsyncSession = Depends(get_db)):
    await logout_user(data.refresh_token, db)


@router.get("/me", response_model=MeResponse)
async def me(current_user=Depends(require_active_user), db: AsyncSession = Depends(get_db)):
    memberships = await get_user_memberships(current_user.id, db)
    return MeResponse(
        user=UserResponse.model_validate(current_user),
        memberships=[MembershipResponse.model_validate(m) for m in memberships],
    )
