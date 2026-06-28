"""Pydantic schemas for authentication endpoints."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class UserRegisterRequest(BaseModel):
    """Payload for user registration."""

    full_name: str = Field(..., min_length=3, max_length=200)
    email: EmailStr
    password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)
    city_id: Optional[int] = None

    @model_validator(mode="after")
    def validate_passwords(self) -> "UserRegisterRequest":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class UserLoginRequest(BaseModel):
    """Payload for user login."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class AdminLoginRequest(BaseModel):
    """Payload for admin login."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """JWT token response payload."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = 1440


class UserResponse(BaseModel):
    """Public user response payload."""

    user_id: int
    full_name: str
    email: str
    city_id: Optional[int]
    city_name: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminResponse(BaseModel):
    """Public admin response payload."""

    admin_id: int
    full_name: str
    email: str
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RegisterResponse(BaseModel):
    """Response returned after a successful registration."""

    message: str
    user: UserResponse
    token: TokenResponse


class LoginResponse(BaseModel):
    """Response returned after a successful user login."""

    message: str
    user: UserResponse
    token: TokenResponse


class AdminLoginResponse(BaseModel):
    """Response returned after a successful admin login."""

    message: str
    admin: AdminResponse
    token: TokenResponse


class MeResponse(BaseModel):
    """Response returned for the authenticated user profile."""

    user_id: int
    full_name: str
    email: str
    city_id: Optional[int]
    city_name: Optional[str]
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
