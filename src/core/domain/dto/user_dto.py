from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class UserProfileDTO(BaseModel):
    id: int
    user_name: str
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[EmailStr]
    balance: float
    discount_rate: float
    language: Optional[str]
    created_at: datetime

class UserCreateDTO(BaseModel):
    user_name: str = Field(min_length=3, max_length=20)
    password: str
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserLoginDTO(BaseModel):
    user_name: str
    password: str

class UserBalanceDTO(BaseModel):
    balance: float

class UserUpdateDTO(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    language: Optional[str] = None