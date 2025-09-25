from abc import ABC, abstractmethod
from typing import List, Optional, Any


class IRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[Any]:
        pass

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Any]:
        pass

    @abstractmethod
    async def create(self, entity: Any) -> Any:
        pass

    @abstractmethod
    async def update(self, entity: Any) -> Optional[Any]:
        pass

    @abstractmethod
    async def delete(self, id: int) -> bool:
        pass


class IUserRepository(IRepository):
    """Интерфейс репозитория пользователей"""

    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[Any]:
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[Any]:
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[Any]:
        pass

    @abstractmethod
    async def get_by_api_key(self, api_key: str) -> Optional[Any]:
        pass

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Any]:
        pass

    @abstractmethod
    async def create(self, entity: Any) -> Any:
        pass

    @abstractmethod
    async def update(self, entity: Any) -> Optional[Any]:
        pass


    @abstractmethod
    async def delete(self, id: int) -> bool:
        pass

    @abstractmethod
    async def update_password(self, user_id: int, password: str) -> Optional[Any]:
        pass

    @abstractmethod
    async def update_balance(self, user_id: int, amount: float) -> Optional[Any]:
        pass

    @abstractmethod
    async def update_api_key(self, user_id: int, api_key: str) -> Optional[Any]:
        pass

    @abstractmethod
    async def user_exists(self, username: str, email: str) -> bool:
        pass

    @abstractmethod
    async def get_password_hash(self, user_id: int) -> Optional[str]:
        pass


class IOrderRepository(IRepository):
    """Интерфейс репозитория заказов"""

    @abstractmethod
    async def get_by_user_id(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Any]:
        pass

    @abstractmethod
    async def get_by_status(self, status: str, skip: int = 0, limit: int = 100) -> List[Any]:
        pass

    @abstractmethod
    async def get_active_orders(self, user_id: int) -> List[Any]:
        pass

    @abstractmethod
    async def update_status(self, order_id: int, status: str, code: Optional[str] = None) -> Optional[Any]:
        pass


class IPaymentRepository(IRepository):
    """Интерфейс репозитория платежей"""
    @abstractmethod
    async def create(self, entity: Any) -> Any:
        pass

    @abstractmethod
    async def update(self, payment_id: int, entity: Any) -> Optional[Any]:
        pass

    @abstractmethod
    async def update_status(self, payment_id: int, status: str, transaction_hash: Optional[str] = None) -> Optional[Any]:
        pass

    @abstractmethod
    async def get_by_user_id(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Any]:
        pass

    @abstractmethod
    async def get_by_invoice_id(self, invoice_id: str) -> Optional[Any]:
        pass


class IPriceRepository:
    """Интерфейс репозитория цен"""

    @abstractmethod
    async def get_service_catalog(self) -> List[Any]:
        """Получить каталог услуг с ценами"""
        pass

    @abstractmethod
    async def get_price_for_service_country(self, service_code: str, country_code: str) -> Optional[Any]:
        """Получить цену для конкретной комбинации сервис-страна"""
        pass

    @abstractmethod
    async def get_services_by_country(self, country_code: str) -> List[Any]:
        """Получить услуги для конкретной страны"""
        pass

    @abstractmethod
    async def get_countries_by_service(self, service_code: str) -> List[Any]:
        """Получить страны для конкретной услуги"""
        pass

    @abstractmethod
    async def get_popular_services(self) -> List[Any]:
        """Получить популярные услуги"""
        pass

    @abstractmethod
    async def get_popular_countries(self) -> List[Any]:
        """Получить популярные страны"""
        pass


class IServiceRepository(IRepository):
    """Интерфейс репозитория сервисов"""

    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Any]:
        pass

    @abstractmethod
    async def get_popular_services(self) -> List[Any]:
        pass

    @abstractmethod
    async def get_services_by_category(self, category: str) -> List[Any]:
        pass


class ICountryRepository(IRepository):
    """Интерфейс репозитория стран"""

    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Any]:
        pass

    @abstractmethod
    async def get_popular_countries(self) -> List[Any]:
        pass

    @abstractmethod
    async def get_countries_by_region(self, region: str) -> List[Any]:
        pass

class IProviderRepository(IRepository):
    """Интерфейс репозитория провайдеров"""

    @abstractmethod
    async def get_active_providers(self) -> List[Any]:
        pass

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Any]:
        pass

class IProviderRouteRepository(IRepository):
    """Интерфейс репозитория маршрутов провайдеров"""

    @abstractmethod
    async def get_best_price_for_service_country(self, service_code: str, country_code: str) -> Optional[Any]:
        pass

    @abstractmethod
    async def get_prices_for_service_country(self, service_code: str, country_code: str) -> List[Any]:
        pass

    @abstractmethod
    async def update_route_stats(self, route_id: int, success: bool, response_time_ms: int) -> bool:
        pass

class IStatusTypeRepository(IRepository):
    """Интерфейс репозитория типов статусов"""

    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Any]:
        pass

    @abstractmethod
    async def get_final_statuses(self) -> List[Any]:
        pass

    @abstractmethod
    async def get_error_statuses(self) -> List[Any]:
        pass