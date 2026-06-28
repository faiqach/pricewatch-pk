"""Authentication routes for user registration, login, admin login, and profile retrieval."""

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.schemas.auth_schemas import (
    AdminLoginRequest,
    AdminResponse,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)

try:
    from app.models import User, AdminUser
except Exception:
    try:
        from app.db.models import User, AdminUser
    except Exception:
        try:
            from app.database.models import User, AdminUser
        except Exception:
            User = Any
            AdminUser = Any

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def register_user(payload: UserRegisterRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    existing_user = db.query(User).filter(User.email == str(payload.email)).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    hashed_password = hash_password(payload.password)
    now = datetime.now(timezone.utc)

    user = User(
        full_name=payload.full_name,
        email=str(payload.email),
        password_hash=hashed_password,
        city_id=payload.city_id,
        is_active=True,
        created_at=now,
        last_login=now,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.user_id), "type": "user"})
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 1440,
        "user": UserResponse.from_orm(user).dict(),
    }


@router.post("/login", response_model=Dict[str, Any])
def login_user(payload: UserLoginRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    user = db.query(User).filter(User.email == str(payload.email)).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    user.last_login = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.user_id), "type": "user"})
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 1440,
        "user": UserResponse.from_orm(user).dict(),
    }


@router.post("/admin/login", response_model=Dict[str, Any])
def admin_login(payload: AdminLoginRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    admin = db.query(AdminUser).filter(AdminUser.email == str(payload.email)).first()
    if not admin or not verify_password(payload.password, admin.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    admin.last_login = datetime.now(timezone.utc)
    db.commit()
    db.refresh(admin)

    token = create_access_token({"sub": str(admin.admin_id), "type": "admin"})
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 1440,
        "admin": AdminResponse.from_orm(admin).dict(),
    }


@router.get("/me", response_model=UserResponse)
def get_me(current_user: Any = Depends(get_current_user)) -> UserResponse:
    return UserResponse.from_orm(current_user)
