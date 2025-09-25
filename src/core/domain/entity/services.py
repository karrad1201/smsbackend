from pydantic import BaseModel
from typing import Optional

class ServiceBase(BaseModel):
    code: str
    name: str
    category: Optional[str] = None
    icon: Optional[str] = None
    is_popular: bool = False
    description: Optional[str] = None

class ServicePublic(ServiceBase):
    class Config:
        from_attributes = True