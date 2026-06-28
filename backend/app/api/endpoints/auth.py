"""Authentication endpoints for PriceWatch PK."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.models import AdminUser, City, User
from app.schemas.auth_schemas import (
    AdminLoginRequest,
    AdminLoginResponse,
    AdminResponse,
    LoginResponse,
    MeResponse,
    RegisterResponse,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)

router = APIRouter()


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    payload: UserRegisterRequest,
    db: Annotated[Session, Depends(get_db)],
) -> RegisterResponse:
    """Register a new user account and return a bearer token."""
    email = payload.email.lower()
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user is not None:
        logger.warning("Registration attempted with existing email {}", email)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = User(
        full_name=payload.full_name.strip(),
        email=email,
        hashed_password=hash_password(payload.password),
        city_id=payload.city_id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token_payload = {"sub": str(user.id), "type": "user", "email": user.email}
    token = create_access_token(token_payload)

    city_name = None
    if user.city_id:
        city = db.query(City).filter(City.id == user.city_id).first()
        city_name = city.name if city else None

    logger.info("User registered successfully: {}", user.email)
    return RegisterResponse(
        message="Account created successfully",
        user=UserResponse(
            user_id=user.id,
            full_name=user.full_name,
            email=user.email,
            city_id=user.city_id,
            city_name=city_name,
            created_at=user.created_at,
        ),
        token=TokenResponse(access_token=token, token_type="bearer", expires_in=1440),
    )


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
def login_user(
    payload: UserLoginRequest,
    db: Annotated[Session, Depends(get_db)],
) -> LoginResponse:
    """Authenticate a user and return a bearer token."""
    email = payload.email.lower()
    user = db.query(User).filter(User.email == email).first()
    if user is None or not verify_password(payload.password, user.hashed_password):
        logger.warning("Failed login attempt for {}", email)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if not user.is_active:
        logger.warning("Deactivated user attempted login {}", email)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account has been deactivated")

    user.last_login = datetime.utcnow()
    db.commit()
    db.refresh(user)

    token_payload = {"sub": str(user.id), "type": "user", "email": user.email}
    token = create_access_token(token_payload)

    city_name = None
    if user.city_id:
        city = db.query(City).filter(City.id == user.city_id).first()
        city_name = city.name if city else None

    logger.info("User login successful: {}", user.email)
    return LoginResponse(
        message="Login successful",
        user=UserResponse(
            user_id=user.id,
            full_name=user.full_name,
            email=user.email,
            city_id=user.city_id,
            city_name=city_name,
            created_at=user.created_at,
        ),
        token=TokenResponse(access_token=token, token_type="bearer", expires_in=1440),
    )


@router.post("/admin/login", response_model=AdminLoginResponse, status_code=status.HTTP_200_OK)
def admin_login(
    payload: AdminLoginRequest,
    db: Annotated[Session, Depends(get_db)],
) -> AdminLoginResponse:
    """Authenticate an admin user and return a bearer token."""
    email = payload.email.lower()
    admin = db.query(AdminUser).filter(AdminUser.email == email).first()
    if admin is None or not verify_password(payload.password, admin.hashed_password):
        logger.warning("Failed admin login attempt for {}", email)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if not admin.is_active:
        logger.warning("Deactivated admin attempted login {}", email)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin account deactivated")

    admin.last_login = datetime.utcnow()
    db.commit()
    db.refresh(admin)

    token_payload = {"sub": str(admin.id), "type": "admin", "role": admin.role, "email": admin.email}
    token = create_access_token(token_payload)

    logger.info("Admin login successful: {}", admin.email)
    return AdminLoginResponse(
        message="Admin login successful",
        admin=AdminResponse(
            admin_id=admin.id,
            full_name=admin.full_name,
            email=admin.email,
            role=admin.role,
            created_at=admin.created_at,
        ),
        token=TokenResponse(access_token=token, token_type="bearer", expires_in=1440),
    )


@router.get("/me", response_model=MeResponse, status_code=status.HTTP_200_OK)
def get_current_user_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> MeResponse:
    """Return the profile of the currently authenticated user."""
    city_name = None
    if current_user.city_id:
        city = db.query(City).filter(City.id == current_user.city_id).first()
        city_name = city.name if city else None

    logger.info("Me endpoint accessed for {}", current_user.email)
    return MeResponse(
        user_id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        city_id=current_user.city_id,
        city_name=city_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout_user(current_user: Annotated[User, Depends(get_current_user)]) -> dict[str, str]:
    """Return a successful logout response for stateless JWT authentication."""
    logger.info("User logout requested by {}", current_user.email)
    return {"message": "Logged out successfully"}
