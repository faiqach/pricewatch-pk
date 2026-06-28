"""Pydantic schemas used by the authentication endpoints."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserRegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    city_id: Optional[int] = None


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 1440


class UserResponse(BaseModel):
    user_id: int
    full_name: str
    email: EmailStr
    city_id: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class AdminResponse(BaseModel):
    admin_id: int
    full_name: str
    email: EmailStr
    role: str
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
