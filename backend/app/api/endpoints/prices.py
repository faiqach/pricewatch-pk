"""Price and catalog endpoints for PriceWatch PK."""

from datetime import datetime, timedelta
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.models import City, Commodity, PriceRecord, User
from app.schemas.price_schemas import (
    CitiesListResponse,
    CityResponse,
    CommoditiesListResponse,
    CommodityResponse,
    ComparePricesResponse,
    LatestPricesResponse,
    PriceHistoryPoint,
    PriceHistoryResponse,
    PriceWithComparisonResponse,
)

router = APIRouter()


@router.get("", response_model=LatestPricesResponse, status_code=status.HTTP_200_OK)
def get_latest_prices(
    city_id: int = Query(...),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50),
    offset: int = Query(0),
    db: Annotated[Session, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
) -> LatestPricesResponse:
    """Return the latest published prices for a city with anomaly information."""
    city = db.query(City).filter(City.id == city_id, City.is_active.is_(True)).first()
    if city is None:
        logger.warning("Prices requested for missing city {}", city_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="City not found")

    latest_subquery = (
        db.query(
            PriceRecord.commodity_id.label("commodity_id"),
            func.max(PriceRecord.recorded_at).label("max_recorded_at"),
        )
        .filter(PriceRecord.city_id == city_id)
        .group_by(PriceRecord.commodity_id)
        .subquery()
    )

    query = (
        db.query(PriceRecord, Commodity)
        .join(Commodity, PriceRecord.commodity_id == Commodity.id)
        .join(latest_subquery, (PriceRecord.commodity_id == latest_subquery.c.commodity_id) & (PriceRecord.recorded_at == latest_subquery.c.max_recorded_at))
        .filter(PriceRecord.city_id == city_id)
        .filter(PriceRecord.price.is_not(None))
    )

    if category:
        query = query.filter(Commodity.category.ilike(category))
    if search:
        query = query.filter(Commodity.name.ilike(f"%{search}%"))

    query = query.order_by(Commodity.name.asc()).offset(offset).limit(limit)
    rows = query.all()

    prices: list[PriceWithComparisonResponse] = []
    anomaly_count = 0
    for price_record, commodity in rows:
        vendor_price = None
        deviation_pct = None
        is_anomaly = False
        trend = None
        trend_reason = None

        vendor_record = (
            db.query(PriceRecord)
            .filter(PriceRecord.commodity_id == commodity.id, PriceRecord.city_id == city_id)
            .order_by(PriceRecord.recorded_at.desc())
            .first()
        )
        if vendor_record is not None:
            vendor_price = float(vendor_record.price)
            if price_record.price and price_record.price != 0:
                deviation_pct = round(((vendor_price - float(price_record.price)) / float(price_record.price)) * 100, 2)
                is_anomaly = deviation_pct > 15.0

        prices.append(
            PriceWithComparisonResponse(
                price_id=price_record.id,
                commodity_id=commodity.id,
                commodity_name=commodity.name,
                commodity_name_urdu=None,
                category=commodity.category.value if hasattr(commodity.category, "value") else str(commodity.category),
                unit=commodity.unit,
                city_id=city.id,
                city_name=city.name,
                price_per_unit=float(price_record.price),
                price_date=price_record.recorded_at,
                status="PUBLISHED",
                source_url=None,
                vendor_price=vendor_price,
                deviation_pct=deviation_pct,
                is_anomaly=is_anomaly,
                trend=trend,
                trend_reason=trend_reason,
            )
        )
        if is_anomaly:
            anomaly_count += 1

    logger.info("Latest prices requested by {} for city {}", current_user.email, city_id)
    return LatestPricesResponse(
        city_id=city.id,
        city_name=city.name,
        date=datetime.utcnow().date().isoformat(),
        prices=prices,
        total_count=len(prices),
        anomaly_count=anomaly_count,
    )


@router.get("/history", response_model=PriceHistoryResponse, status_code=status.HTTP_200_OK)
def get_price_history(
    city_id: int = Query(...),
    commodity_id: int = Query(...),
    days: int = Query(30, ge=1, le=90),
    db: Annotated[Session, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
) -> PriceHistoryResponse:
    """Return historical prices for a single commodity within the requested number of days."""
    city = db.query(City).filter(City.id == city_id, City.is_active.is_(True)).first()
    commodity = db.query(Commodity).filter(Commodity.id == commodity_id, Commodity.is_active.is_(True)).first()
    if city is None or commodity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="City or commodity not found")

    cutoff = datetime.utcnow() - timedelta(days=days)
    records = (
        db.query(PriceRecord)
        .filter(PriceRecord.city_id == city_id)
        .filter(PriceRecord.commodity_id == commodity_id)
        .filter(PriceRecord.recorded_at >= cutoff)
        .order_by(PriceRecord.recorded_at.asc())
        .all()
    )

    if not records:
        logger.warning("No price history for commodity {} in city {}", commodity_id, city_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No price history found")

    history = [
        PriceHistoryPoint(date=record.recorded_at.date().isoformat(), price=float(record.price), price_id=record.id)
        for record in records
    ]
    values = [item.price for item in history]
    logger.info("Price history requested by {} for commodity {}", current_user.email, commodity_id)
    return PriceHistoryResponse(
        commodity_id=commodity.id,
        commodity_name=commodity.name,
        city_id=city.id,
        city_name=city.name,
        unit=commodity.unit,
        history=history,
        min_price=min(values),
        max_price=max(values),
        avg_price=round(sum(values) / len(values), 2),
        data_points=len(history),
    )


@router.get("/compare", response_model=ComparePricesResponse, status_code=status.HTTP_200_OK)
def compare_prices(
    city_id: int = Query(...),
    commodity_id: int = Query(...),
    db: Annotated[Session, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
) -> ComparePricesResponse:
    """Compare the latest official price to the latest vendor price for a commodity."""
    city = db.query(City).filter(City.id == city_id, City.is_active.is_(True)).first()
    commodity = db.query(Commodity).filter(Commodity.id == commodity_id, Commodity.is_active.is_(True)).first()
    if city is None or commodity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="City or commodity not found")

    official = (
        db.query(PriceRecord)
        .filter(PriceRecord.city_id == city_id, PriceRecord.commodity_id == commodity_id)
        .order_by(PriceRecord.recorded_at.desc())
        .first()
    )
    if official is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No price data found")

    vendor = (
        db.query(PriceRecord)
        .filter(PriceRecord.city_id == city_id, PriceRecord.commodity_id == commodity_id)
        .order_by(PriceRecord.recorded_at.desc())
        .first()
    )
    vendor_price = float(vendor.price) if vendor else None
    deviation_pct = None
    is_anomaly = False
    if vendor_price is not None and official.price not in (None, 0):
        deviation_pct = round(((vendor_price - float(official.price)) / float(official.price)) * 100, 2)
        is_anomaly = deviation_pct > 15.0

    logger.info("Price comparison requested by {} for commodity {}", current_user.email, commodity_id)
    return ComparePricesResponse(
        commodity_id=commodity.id,
        commodity_name=commodity.name,
        unit=commodity.unit,
        official_price=float(official.price),
        vendor_price=vendor_price,
        deviation_pct=deviation_pct,
        is_anomaly=is_anomaly,
        city_id=city.id,
        city_name=city.name,
        last_updated=official.recorded_at,
    )


@router.get("/cities", response_model=CitiesListResponse, status_code=status.HTTP_200_OK)
def get_cities(db: Annotated[Session, Depends(get_db)] = None) -> CitiesListResponse:
    """Return all active cities."""
    cities = db.query(City).filter(City.is_active.is_(True)).order_by(City.name.asc()).all()
    logger.info("Cities catalog requested")
    return CitiesListResponse(cities=[CityResponse(city_id=city.id, name=city.name, province=city.province, is_active=city.is_active) for city in cities], total=len(cities))


@router.get("/commodities", response_model=CommoditiesListResponse, status_code=status.HTTP_200_OK)
def get_commodities(
    category: Optional[str] = Query(None),
    db: Annotated[Session, Depends(get_db)] = None,
) -> CommoditiesListResponse:
    """Return all active commodities, optionally filtered by category."""
    query = db.query(Commodity).filter(Commodity.is_active.is_(True))
    if category:
        query = query.filter(Commodity.category.ilike(category))
    commodities = query.order_by(Commodity.category.asc(), Commodity.name.asc()).all()
    categories = sorted({commodity.category.value if hasattr(commodity.category, "value") else str(commodity.category) for commodity in commodities})
    logger.info("Commodities catalog requested")
    return CommoditiesListResponse(
        commodities=[
            CommodityResponse(
                commodity_id=commodity.id,
                name=commodity.name,
                name_urdu=None,
                category=commodity.category.value if hasattr(commodity.category, "value") else str(commodity.category),
                unit=commodity.unit,
                is_active=commodity.is_active,
            )
            for commodity in commodities
        ],
        total=len(commodities),
        categories=categories,
    )


@router.get("/summary", status_code=status.HTTP_200_OK)
def get_price_summary(
    city_id: int = Query(...),
    db: Annotated[Session, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
) -> dict:
    """Return a dashboard summary for the requested city."""
    city = db.query(City).filter(City.id == city_id, City.is_active.is_(True)).first()
    if city is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="City not found")

    published_prices = db.query(PriceRecord).filter(PriceRecord.city_id == city_id).count()
    prices = db.query(PriceRecord).filter(PriceRecord.city_id == city_id).all()
    anomaly_count = 0
    rising_count = 0
    falling_count = 0
    stable_count = 0
    for record in prices:
        if record.price is not None:
            if record.price > 0:
                stable_count += 1
    logger.info("Price summary requested by {} for city {}", current_user.email, city_id)
    return {
        "city": city.name,
        "date": datetime.utcnow().date().isoformat(),
        "total_commodities": db.query(Commodity).filter(Commodity.is_active.is_(True)).count(),
        "published_prices": published_prices,
        "anomaly_count": anomaly_count,
        "rising_count": rising_count,
        "falling_count": falling_count,
        "stable_count": stable_count,
        "last_scrape": None,
    }
