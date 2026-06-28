"""Main FastAPI application entry point for the PriceWatch PK backend."""

from fastapi import FastAPI

from app.api.endpoints.auth import router as auth_router

app = FastAPI(title="PriceWatch PK", version="1.0.0")
app.include_router(auth_router)
