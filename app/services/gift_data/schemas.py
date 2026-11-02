"""Validation schemas for TG Gifts public datasets."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from pydantic import BaseModel, Field


class CollectionDayObservation(BaseModel):
    date: str
    floor_gram: Decimal
    recent_sales: Optional[str] = None
    price_kind: Optional[str] = None


class NormalizedCollection(BaseModel):
    slug: str
    name: str
    latest_date: str
    latest_floor_gram: Decimal
    recent_sales: Optional[str] = None
    history: list[CollectionDayObservation] = Field(default_factory=list)


class ModelDayObservation(BaseModel):
    date: str
    floor_gram: Decimal
    buy_now_listings: Optional[int] = None


class NormalizedModel(BaseModel):
    collection_slug: str
    name: str
    slug: Optional[str] = None
    rarity_permille: Optional[Decimal] = None
    rarity_pct: Optional[Decimal] = None
    latest_date: str
    latest_floor_gram: Decimal
    buy_now_listings: Optional[int] = None
    history: list[ModelDayObservation] = Field(default_factory=list)


class IndexSeriesPoint(BaseModel):
    date: str
    value: Decimal
    change_pct: Optional[Decimal] = None
    constituents: Optional[int] = None


class IndexConstituent(BaseModel):
    slug: str
    name: str
    floor_prev_gram: Optional[Decimal] = None
    floor_gram: Optional[Decimal] = None
    change_pct: Optional[Decimal] = None
    recent_sales: Optional[str] = None
    weight_pct: Optional[Decimal] = None


class NormalizedIndex(BaseModel):
    name: str
    symbol: str
    method_version: str
    unit: str
    source: str
    license: str
    latest_date: str
    latest_value: Decimal
    change_1d_pct: Optional[Decimal] = None
    change_7d_pct: Optional[Decimal] = None
    constituents_count: Optional[int] = None
    series: list[IndexSeriesPoint] = Field(default_factory=list)
    constituents: list[IndexConstituent] = Field(default_factory=list)
