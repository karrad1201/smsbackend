from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

class ProviderRoute(BaseModel):
    id: int
    provider_id: int
    country_code: str
    service_code: str
    provider_country_code: str
    provider_service_code: str
    cost_price: Decimal
    client_price: Decimal
    vip_client_price: Decimal
    min_margin_percent: Decimal
    available_count: int
    max_daily_limit: Optional[int] = None
    priority: int = 100
    rating_score: float = 50.0
    success_rate: float = 0.0
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BestProviderPrice(BaseModel):
    service_code: str
    country_code: str
    price: Decimal
    vip_price: Optional[Decimal] = None
    provider_id: int
    provider_name: str
    available: bool = True
    rating: float = 50.0

    class Config:
        from_attributes = True