from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_active_user
from app.core.rate_limit import forgot_password_rate_limit, login_rate_limit, register_rate_limit
from app.db.session import get_db
from app.schemas.auth import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LogoutRequest,
    MeResponse,
    MembershipResponse,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    ResetPasswordResponse,
    TokenResponse,
    UserResponse,
)
from app.services.auth import (
    AuthError,
    get_user_memberships,
    login_user,
    logout_user,
    refresh_tokens,
    register_user,
    request_password_reset,
    reset_password,
)

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


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(forgot_password_rate_limit),
):
    # Always returns the same generic response regardless of whether the
    # email exists — request_password_reset() itself contains the no-op
    # branch for unknown emails, so there is nothing to branch on here.
    await request_password_reset(data.email, db)
    return ForgotPasswordResponse()


@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password_endpoint(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        await reset_password(data.token, data.new_password, db)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return ResetPasswordResponse()


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
