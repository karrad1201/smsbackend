from decimal import Decimal
from typing import List, Optional, Dict, Any
from src.core.domain.repository.interfaces import IPriceRepository
from src.core.domain.entity.service_price import ServicePrice
from src.core.exceptions.exceptions import NotFoundException


class PriceService:
    def __init__(self, price_repo: IPriceRepository):
        self.price_repo = price_repo

    async def get_full_catalog(self) -> List[ServicePrice]:
        """
        Получить полный каталог услуг с минимальными ценами и доступностью.
        Используется для отображения общего прайс-листа.
        """
        return await self.price_repo.get_service_catalog()

    async def get_service_price(
        self, service_code: str, country_code: str
    ) -> Optional[ServicePrice]:
        """
        Получить лучшую цену для конкретной услуги в указанной стране.
        Используется при оформлении заказа.
        """
        if not service_code or not country_code:
            raise KeyError("Service code and country code are required")

        price = await self.price_repo.get_price_for_service_country(
            service_code, country_code
        )
        if not price:
            raise NotFoundException
        return price

    async def list_services_by_country(self, country_code: str) -> List[ServicePrice]:
        """
        Получить все услуги, доступные для указанной страны.
        Используется в фильтрах на фронтенде.
        """
        if not country_code:
            raise KeyError("Country code is required")

        return await self.price_repo.get_services_by_country(country_code)

    async def list_countries_by_service(self, service_code: str) -> List[ServicePrice]:
        """
        Получить все страны, где доступна указанная услуга.
        Используется при выборе страны для услуги.
        """
        if not service_code:
            raise KeyError("Service code is required")

        return await self.price_repo.get_countries_by_service(service_code)

    async def get_popular_services(self) -> List[ServicePrice]:
        """
        Получить список популярных услуг (помеченных как is_popular).
        Для главной страницы или быстрого выбора.
        """
        return await self.price_repo.get_popular_services()

    async def get_popular_countries(self) -> List[ServicePrice]:
        """
        Получить список популярных стран (помеченных как is_popular).
        Для главной страницы или быстрого выбора.
        """
        return await self.price_repo.get_popular_countries()

    async def get_availability_stats(self) -> Dict[str, Any]:
        """
        Получить статистику по доступным услугам и странам.
        Для админ-панели или дашборда.
        """
        return await self.price_repo.get_available_services_countries()

    async def get_detailed_prices(
        self, service_code: str, country_code: str
    ) -> List[Any]:
        """
        Получить детализированный список цен от всех провайдеров для услуги и страны.
        Для сравнения цен и выбора провайдера.
        """
        if not service_code or not country_code:
            raise KeyError("Service code and country code are required")

        return await self.price_repo.get_detailed_prices_for_service_country(
            service_code, country_code
        )