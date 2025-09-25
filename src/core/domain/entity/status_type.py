from pydantic import BaseModel
from typing import Optional

class StatusType(BaseModel):
    id: int
    code: str
    name_en: str
    name_ru: Optional[str] = None
    description: Optional[str] = None
    is_final: bool = False
    is_error: bool = False

    class Config:
        from_attributes = True