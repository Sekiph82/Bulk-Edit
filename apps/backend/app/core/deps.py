from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt

from app.core.security import decode_access_token
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

_bearer = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
):
    from app.models.user import User

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def require_active_user(user=Depends(get_current_user)):
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account inactive")
    return user


async def require_superuser(user=Depends(require_active_user)):
    if not user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Superuser required")
    return user


async def get_current_org_id(
    user=Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> str:
    from app.models.organization_member import OrganizationMember

    result = await db.execute(
        select(OrganizationMember)
        .where(OrganizationMember.user_id == user.id, OrganizationMember.role == "owner")
        .limit(1)
    )
    member = result.scalar_one_or_none()
    if not member:
        result = await db.execute(
            select(OrganizationMember).where(OrganizationMember.user_id == user.id).limit(1)
        )
        member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No organization found for user")
    return member.organization_id
