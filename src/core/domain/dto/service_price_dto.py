from pydantic import BaseModel
from typing import Optional, List

class ServiceCatalogDTO(BaseModel):
    service_code: str
    service_name: str
    countries: List['ServiceCountryPriceDTO']

class ServiceCountryPriceDTO(BaseModel):
    country_code: str
    country_name: str
    price: float
    vip_price: Optional[float] = None
    available: bool = True

class CountryServicesDTO(BaseModel):
    country_code: str
    country_name: str
    services: List['ServicePriceInfoDTO']

class ServicePriceInfoDTO(BaseModel):
    service_code: str
    service_name: str
    price: float
    available: bool

class OrderPriceDTO(BaseModel):
    service_code: str
    country_code: str
    price: float
    service_name: str
    country_name: str