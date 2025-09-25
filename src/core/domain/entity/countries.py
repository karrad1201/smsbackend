from pydantic import BaseModel
from typing import Optional

class CountryBase(BaseModel):
    code: str
    name_ru: str
    name_en: Optional[str] = None
    iso_code: Optional[str] = None
    region: Optional[str] = None
    is_popular: bool = False

class CountryPublic(CountryBase):
    class Config:
        from_attributes = True