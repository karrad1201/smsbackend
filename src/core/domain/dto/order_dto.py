from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from src.core.domain.entity.orders import OrderStatus

class OrderDTO(BaseModel):
    id: int
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