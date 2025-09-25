from typing import List, Dict
from src.core.domain.entity.service_price import ServicePrice
from src.core.domain.dto.service_price_dto import (
    ServiceCatalogDTO, ServiceCountryPriceDTO,
    CountryServicesDTO, ServicePriceInfoDTO, OrderPriceDTO
)


class ServicePriceMapper:

    @staticmethod
    def to_catalog_dto(
            prices: List[ServicePrice],
            service_names: Dict[str, str],
            country_names: Dict[str, str]
    ) -> List[ServiceCatalogDTO]:
        catalog = {}

        for price in prices:
            if price.service_code not in catalog:
                catalog[price.service_code] = ServiceCatalogDTO(
                    service_code=price.service_code,
                    service_name=service_names.get(price.service_code, price.service_code),
                    countries=[]
                )

            catalog[price.service_code].countries.append(
                ServiceCountryPriceDTO(
                    country_code=price.country_code,
                    country_name=country_names.get(price.country_code, price.country_code),
                    price=price.price,
                    vip_price=price.vip_price,
                    available=price.available
                )
            )

        return list(catalog.values())

    @staticmethod
    def to_country_services_dto(
            prices: List[ServicePrice],
            service_names: Dict[str, str],
            country_names: Dict[str, str]
    ) -> List[CountryServicesDTO]:
        countries = {}

        for price in prices:
            if price.country_code not in countries:
                countries[price.country_code] = CountryServicesDTO(
                    country_code=price.country_code,
                    country_name=country_names.get(price.country_code, price.country_code),
                    services=[]
                )

            countries[price.country_code].services.append(
                ServicePriceInfoDTO(
                    service_code=price.service_code,
                    service_name=service_names.get(price.service_code, price.service_code),
                    price=price.price,
                    available=price.available
                )
            )

        return list(countries.values())

    @staticmethod
    def to_order_price_dto(
            price: ServicePrice,
            service_name: str,
            country_name: str
    ) -> 'OrderPriceDTO':
        return OrderPriceDTO(
            service_code=price.service_code,
            country_code=price.country_code,
            price=price.price,
            service_name=service_name,
            country_name=country_name
        )