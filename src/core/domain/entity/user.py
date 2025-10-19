from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from enum import Enum

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

class User(BaseModel):
    id: int
    user_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    balance: float
    language: Optional[str] = None
    discount_rate: float = 0.0
    is_admin: bool = False

    is_verified: bool = True
    is_banned: bool = False
    client_note: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    api_key: Optional[str] = None

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    user_name: str
    password: str
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language: Optional[str] = None

class UserPrivate(User):
    password_hash: str