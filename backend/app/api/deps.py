"""FastAPI dependencies for authentication and authorization."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models.models import AdminUser, User
from loguru import logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Return the currently authenticated user from the JWT."""
    try:
        payload = decode_token(token)
    except HTTPException as exc:
        logger.warning("Authentication failed while fetching current user")
        raise exc from None

    if payload.get("type") != "user":
        logger.warning("Token type mismatch while resolving current user")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired or invalid")

    try:
        user_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        logger.warning("Invalid subject claim in access token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired or invalid") from None

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        logger.warning("User not found for token subject {}", user_id)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired or invalid")

    if not user.is_active:
        logger.warning("Inactive user attempted access: {}", user.email)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account has been deactivated")

    return user


def get_current_admin(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> AdminUser:
    """Return the currently authenticated admin from the JWT."""
    try:
        payload = decode_token(token)
    except HTTPException as exc:
        logger.warning("Authentication failed while fetching current admin")
        raise exc from None

    if payload.get("type") != "admin":
        logger.warning("Token type mismatch while resolving current admin")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired or invalid")

    try:
        admin_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        logger.warning("Invalid subject claim in admin token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired or invalid") from None

    admin = db.query(AdminUser).filter(AdminUser.id == admin_id).first()
    if admin is None:
        logger.warning("Admin not found for token subject {}", admin_id)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired or invalid")

    if not admin.is_active:
        logger.warning("Inactive admin attempted access: {}", admin.email)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin account deactivated")

    return admin


def get_current_super_admin(admin: Annotated[AdminUser, Depends(get_current_admin)]) -> AdminUser:
    """Ensure the current admin has super-admin permissions."""
    if admin.role != "super_admin":
        logger.warning("Non-super-admin attempted super-admin access: {}", admin.email)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super admin access required")
    return admin
