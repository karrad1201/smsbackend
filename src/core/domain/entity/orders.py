from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum

class OrderStatus(str, Enum):
    WAITING_CODE = "WAITING_CODE"
    PENDING_ORDER = "PENDING_ORDER"
    WAITING_RETRY_CODE = "WAITING_RETRY_CODE"
    COMPLETED = "COMPLETED"
    USER_CANCELLED_REFUNDED = "USER_CANCELLED_REFUNDED"
    PROVIDER_CANCELLED_REFUNDED = "PROVIDER_CANCELLED_REFUNDED"
    NO_NUMBERS_REFUNDED = "NO_NUMBERS_REFUNDED"

class Order(BaseModel):
    id: int
    user_id: int
    provider_id: Optional[int] = None
    number: Optional[str] = None
    activ_id: Optional[str] = None
    code: Optional[str] = None
    service: str
    price: float
    country_code: str
    status: OrderStatus
    status_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    provider_cost_price: Optional[float] = None
    client_ip: Optional[str] = None

    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    service: str
    country_code: str
    price: float
    provider_id: Optional[int] = None

class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    code: Optional[str] = None
    number: Optional[str] = None
    status_id: Optional[int] = None