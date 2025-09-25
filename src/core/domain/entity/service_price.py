from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal
from .provider_route import BestProviderPrice

class ServicePrice(BaseModel):
    service_code: str
    country_code: str
    price: float
    vip_price: Optional[float] = None
    available: bool = True
    country_name: Optional[str] = None
    service_name: Optional[str] = None

    class Config:
        from_attributes = True

class ServicePriceDetailed(BaseModel):
    service_code: str
    country_code: str
    best_price: BestProviderPrice
    all_prices: List[BestProviderPrice]
    country_name: Optional[str] = None
    service_name: Optional[str] = None

    class Config:
        from_attributes = True

class ServicePriceCreate(BaseModel):
    service_code: str
    country_code: str
    price: float

class ServicePriceUpdate(BaseModel):
    price: Optional[float] = None
    vip_price: Optional[float] = None
    available: Optional[bool] = None