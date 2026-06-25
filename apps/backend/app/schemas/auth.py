from pydantic import BaseModel, EmailStr, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str = ""
    organization_name: str = ""

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    is_active: bool
    is_verified: bool
    is_superuser: bool

    model_config = {"from_attributes": True}


class OrganizationResponse(BaseModel):
    id: str
    name: str
    owner_id: str

    model_config = {"from_attributes": True}


class MembershipResponse(BaseModel):
    id: str
    organization_id: str
    user_id: str
    role: str

    model_config = {"from_attributes": True}


class MeResponse(BaseModel):
    user: UserResponse
    memberships: list[MembershipResponse]
