from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.prices import router as prices_router
from app.core.config import settings
from app.core.database import Base, engine
from app.db.seed import seed_data
from app.models import models

app = FastAPI(title=settings.app_name, version=settings.app_version, debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event() -> None:
    try:
        Base.metadata.create_all(bind=engine)
        seed_data()
    except Exception as exc:  # pragma: no cover - defensive for local development
        logger.warning("Database startup skipped: {}", exc)


app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(prices_router, prefix="/prices", tags=["Prices"])
app.include_router(prices_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version}


@app.get("/")
def root() -> dict:
    return {"message": "PriceWatch PK API is running"}
