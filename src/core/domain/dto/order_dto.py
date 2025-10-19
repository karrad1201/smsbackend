# order_dto.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from src.core.domain.entity.orders import OrderStatus

class ExternalAPIResponse(BaseModel):
    status_code: str
    activationId: Optional[str] = None
    phoneNumber: Optional[str] = None
    priceCharged: Optional[float] = None
    activationTime: Optional[str] = None
    countryCode: Optional[str] = None
    value: Optional[str] = None
    code: Optional[str] = None

class OrderDTO(BaseModel):
    id: str
    service: str
    service_name: Optional[str] = None
    country_code: str
    country_name: Optional[str] = None
    phone_number: Optional[str] = None
    price: float
    status: OrderStatus
    provider_id: Optional[int] = None
    provider_name: Optional[str] = None
    created_at: datetime
    code: Optional[str] = None
    activ_id: Optional[str] = None
    updated_at: Optional[datetime] = None
    external_status: Optional[str] = None
    activation_time: Optional[str] = None
    user_id: int

    class Config:
        from_attributes = True

class OrderCreateDTO(BaseModel):
    service: str
    country_code: str

class OrderStatusDTO(BaseModel):
    status: OrderStatus
    code: Optional[str] = None
    status_id: Optional[int] = None

class OrderListDTO(BaseModel):
    orders: list[OrderDTO]
    total: int
    page: int
    size: int

class OrderPollResponse(BaseModel):
    status: OrderStatus
    code: Optional[str] = None
    phone_number: Optional[str] = None
    external_status: str