from src.core.domain.repository.interfaces import IUserRepository, IProviderRepository, IStatusTypeRepository, \
    IOrderRepository, IPaymentRepository, IServiceRepository, ICountryRepository, IProviderRouteRepository, \
    IPriceRepository
from src.infrastructure.repository.user_repository import UserRepository
from src.infrastructure.repository.provider_repository import ProviderRepository
from src.infrastructure.repository.status_type_repository import StatusTypeRepository
from src.infrastructure.repository.order_repository import OrderRepository
from src.infrastructure.repository.payment_repository import PaymentRepository
from src.infrastructure.repository.service_repository import ServiceRepository
from src.infrastructure.repository.country_repository import CountryRepository
from src.infrastructure.repository.provider_route_repository import ProviderRouteRepository
from src.infrastructure.repository.price_repository import PriceRepository
from src.infrastructure.database.connection import get_db_session
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession


def get_user_repo(session: AsyncSession = Depends(get_db_session)) -> IUserRepository:
    return UserRepository(session=session)


def get_provider_repo(session: AsyncSession = Depends(get_db_session)) -> IProviderRepository:
    return ProviderRepository(session=session)


def get_status_type_repo(session: AsyncSession = Depends(get_db_session)) -> IStatusTypeRepository:
    return StatusTypeRepository(session=session)


def get_order_repo(session: AsyncSession = Depends(get_db_session)) -> IOrderRepository:
    return OrderRepository(session=session)


def get_payment_repo(session: AsyncSession = Depends(get_db_session)) -> IPaymentRepository:
    return PaymentRepository(session=session)


def get_service_repo(session: AsyncSession = Depends(get_db_session)) -> IServiceRepository:
    return ServiceRepository(session=session)


def get_country_repo(session: AsyncSession = Depends(get_db_session)) -> ICountryRepository:
    return CountryRepository(session=session)


def get_provider_route_repo(session: AsyncSession = Depends(get_db_session)) -> IProviderRouteRepository:
    return ProviderRouteRepository(session=session)


def get_price_repo(session: AsyncSession = Depends(get_db_session)) -> IPriceRepository:
    return PriceRepository(session=session)


__all__ = [
    "get_user_repo",
    "get_provider_repo",
    "get_status_type_repo",
    "get_order_repo",
    "get_payment_repo",
    "get_service_repo",
    "get_country_repo",
    "get_provider_route_repo",
    "get_price_repo"
]
