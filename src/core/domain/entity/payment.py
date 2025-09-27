from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class PaymentBase(BaseModel):
    user_id: int
    amount: float
    cash_register: Optional[str] = None
    invoice_id: Optional[str] = None
    status: PaymentStatus = PaymentStatus.PENDING
    transaction_hash: Optional[str] = None

class PaymentCreate(PaymentBase):
    pass

class PaymentUpdate(BaseModel):
    status: Optional[PaymentStatus] = None
    transaction_hash: Optional[str] = None
    invoice_id: Optional[str] = None
    cash_register: Optional[str] = None

class Payment(PaymentBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PaymentResponse(BaseModel):
    payment_url: Optional[str] = None
    invoice_id: str
    status: PaymentStatus

class PaymentWebhookData(BaseModel):
    """Модель для данных вебхука от платежных систем"""
    invoice_id: str
    transaction_id: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    status: PaymentStatus
    signature: Optional[str] = None
    raw_data: Optional[dict] = None
