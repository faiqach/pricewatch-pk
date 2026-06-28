"""Pydantic schemas for price and catalog endpoints."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CityResponse(BaseModel):
    """Public city response."""

    city_id: int
    name: str
    province: str
    is_active: bool


class CommodityResponse(BaseModel):
    """Public commodity response."""

    commodity_id: int
    name: str
    name_urdu: Optional[str] = None
    category: str
    unit: str
    is_active: bool


class PriceResponse(BaseModel):
    """Price payload returned for the latest price list."""

    price_id: int
    commodity_id: int
    commodity_name: str
    commodity_name_urdu: Optional[str] = None
    category: str
    unit: str
    city_id: int
    city_name: str
    price_per_unit: float
    price_date: datetime
    status: str
    source_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PriceWithComparisonResponse(PriceResponse):
    """Latest price payload with comparison and anomaly data."""

    vendor_price: Optional[float] = None
    deviation_pct: Optional[float] = None
    is_anomaly: bool = False
    trend: Optional[str] = None
    trend_reason: Optional[str] = None


class PriceHistoryPoint(BaseModel):
    """Single point in a commodity price history."""

    date: str
    price: float
    price_id: int


class PriceHistoryResponse(BaseModel):
    """Response containing historical prices for a commodity."""

    commodity_id: int
    commodity_name: str
    city_id: int
    city_name: str
    unit: str
    history: List[PriceHistoryPoint]
    min_price: float
    max_price: float
    avg_price: float
    data_points: int


class LatestPricesResponse(BaseModel):
    """Response for the latest price snapshot for a city."""

    city_id: int
    city_name: str
    date: str
    prices: List[PriceWithComparisonResponse]
    total_count: int
    anomaly_count: int


class ComparePricesResponse(BaseModel):
    """Response for official vs vendor comparison."""

    commodity_id: int
    commodity_name: str
    unit: str
    official_price: float
    vendor_price: Optional[float] = None
    deviation_pct: Optional[float] = None
    is_anomaly: bool = False
    city_id: int
    city_name: str
    last_updated: datetime


class CitiesListResponse(BaseModel):
    """Paged or simple list of active cities."""

    cities: List[CityResponse]
    total: int


class CommoditiesListResponse(BaseModel):
    """Response wrapper for commodities and categories."""

    commodities: List[CommodityResponse]
    total: int
    categories: List[str]
