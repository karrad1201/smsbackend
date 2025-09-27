from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case
import os
from typing import List, Optional, Dict, Any
from decimal import Decimal

from src.core.domain.repository.interfaces import IPriceRepository
from src.core.domain.entity.service_price import ServicePrice
from src.infrastructure.database.schemas import (
    ProviderRoutesORM,
    ServiceReferenceORM,
    CountryReferenceORM,
    ProviderORM
)
from src.core.logging_config import get_logger


class PriceRepository(IPriceRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = get_logger(__name__)

    async def get_service_catalog(self) -> List[ServicePrice]:
        try:
            if os.environ.get("TESTING") == "1":
                is_available_expr = func.MAX(
                    case(
                        (
                            and_(
                                ProviderRoutesORM.is_active == True,
                                ProviderRoutesORM.available_count > 0
                            ),
                            1
                        ),
                        else_=0
                    )
                ).label('is_available')
            else:
                is_available_expr = func.bool_or(
                    and_(
                        ProviderRoutesORM.is_active == True,
                        ProviderRoutesORM.available_count > 0
                    )
                ).label('is_available')

            subquery = (
                select(
                    ProviderRoutesORM.service_code,
                    ProviderRoutesORM.country_code,
                    func.min(ProviderRoutesORM.client_price).label('min_price'),
                    func.min(ProviderRoutesORM.vip_client_price).label('min_vip_price'),
                    func.max(ProviderRoutesORM.available_count).label('max_available'),
                    is_available_expr
                )
                .where(ProviderRoutesORM.is_active == True)
                .group_by(
                    ProviderRoutesORM.service_code,
                    ProviderRoutesORM.country_code
                )
                .subquery()
            )

            query = (
                select(
                    subquery.c.service_code,
                    subquery.c.country_code,
                    subquery.c.min_price.label('price'),
                    subquery.c.min_vip_price.label('vip_price'),
                    subquery.c.is_available.label('available'),
                    ServiceReferenceORM.name.label('service_name'),
                    CountryReferenceORM.name_ru.label('country_name')
                )
                .select_from(subquery)
                .join(
                    ServiceReferenceORM,
                    subquery.c.service_code == ServiceReferenceORM.code,
                    isouter=True
                )
                .join(
                    CountryReferenceORM,
                    subquery.c.country_code == CountryReferenceORM.code,
                    isouter=True
                )
                .where(subquery.c.min_price > 0)
                .order_by(
                    ServiceReferenceORM.name,
                    CountryReferenceORM.name_ru
                )
            )

            result = await self.session.execute(query)
            rows = result.all()

            catalog = []
            for row in rows:
                try:
                    service_price = ServicePrice(
                        service_code=row.service_code,
                        country_code=row.country_code,
                        price=Decimal(str(row.price)) if row.price else Decimal('0.0'),
                        vip_price=float(row.vip_price) if row.vip_price else None,
                        available=bool(row.available),
                        service_name=row.service_name or row.service_code,
                        country_name=row.country_name or row.country_code
                    )
                    catalog.append(service_price)
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"Skipping invalid price data for {row.service_code}/{row.country_code}: {e}")
                    continue

            self.logger.info(f"Retrieved {len(catalog)} price combinations")
            return catalog

        except Exception as e:
            self.logger.error(f"Error getting service catalog: {e}")
            raise

    async def get_price_for_service_country(self, service_code: str, country_code: str) -> Optional[ServicePrice]:
        try:
            query = (
                select(
                    ProviderRoutesORM.service_code,
                    ProviderRoutesORM.country_code,
                    ProviderRoutesORM.client_price.label('price'),
                    ProviderRoutesORM.vip_client_price.label('vip_price'),
                    and_(
                        ProviderRoutesORM.is_active == True,
                        ProviderRoutesORM.available_count > 0
                    ).label('available'),
                    ServiceReferenceORM.name.label('service_name'),
                    CountryReferenceORM.name_ru.label('country_name'),
                    ProviderRoutesORM.provider_id,
                    ProviderORM.name.label('provider_name')
                )
                .select_from(ProviderRoutesORM)
                .join(
                    ServiceReferenceORM,
                    ProviderRoutesORM.service_code == ServiceReferenceORM.code,
                    isouter=True
                )
                .join(
                    CountryReferenceORM,
                    ProviderRoutesORM.country_code == CountryReferenceORM.code,
                    isouter=True
                )
                .join(
                    ProviderORM,
                    ProviderRoutesORM.provider_id == ProviderORM.id,
                    isouter=True
                )
                .where(
                    and_(
                        ProviderRoutesORM.service_code == service_code,
                        ProviderRoutesORM.country_code == country_code,
                        ProviderRoutesORM.is_active == True,
                        ProviderRoutesORM.client_price > 0
                    )
                )
                .order_by(
                    ProviderRoutesORM.client_price.asc(),
                    ProviderRoutesORM.rating_score.desc(),
                    ProviderRoutesORM.available_count.desc()
                )
                .limit(1)
            )

            result = await self.session.execute(query)
            row = result.first()

            if not row:
                self.logger.info(f"No active prices found for {service_code}/{country_code}")
                return None

            return ServicePrice(
                service_code=row.service_code,
                country_code=row.country_code,
                price=Decimal(str(row.price)) if row.price else Decimal('0.0'),
                vip_price=float(row.vip_price) if row.vip_price else None,
                available=bool(row.available),
                service_name=row.service_name or service_code,
                country_name=row.country_name or country_code
            )

        except Exception as e:
            self.logger.error(f"Error getting price for {service_code}/{country_code}: {e}")
            raise

    async def get_services_by_country(self, country_code: str) -> List[ServicePrice]:
        try:
            if os.environ.get("TESTING") == "1":
                # SQLite-совместимая версия
                is_available_expr = func.MAX(
                    case(
                        (
                            and_(
                                ProviderRoutesORM.is_active == True,
                                ProviderRoutesORM.available_count > 0
                            ),
                            1
                        ),
                        else_=0
                    )
                ).label('is_available')
            else:
                # PostgreSQL версия
                is_available_expr = func.bool_or(
                    and_(
                        ProviderRoutesORM.is_active == True,
                        ProviderRoutesORM.available_count > 0
                    )
                ).label('is_available')

            subquery = (
                select(
                    ProviderRoutesORM.service_code,
                    ProviderRoutesORM.country_code,
                    func.min(ProviderRoutesORM.client_price).label('min_price'),
                    func.min(ProviderRoutesORM.vip_client_price).label('min_vip_price'),
                    func.max(ProviderRoutesORM.available_count).label('max_available'),
                    is_available_expr
                )
                .where(ProviderRoutesORM.is_active == True)
                .group_by(
                    ProviderRoutesORM.service_code,
                    ProviderRoutesORM.country_code
                )
                .subquery()
            )

            query = (
                select(
                    subquery.c.service_code,
                    subquery.c.country_code,
                    subquery.c.min_price.label('price'),
                    subquery.c.min_vip_price.label('vip_price'),
                    subquery.c.is_available.label('available'),
                    ServiceReferenceORM.name.label('service_name'),
                    CountryReferenceORM.name_ru.label('country_name')
                )
                .select_from(subquery)
                .join(
                    ServiceReferenceORM,
                    subquery.c.service_code == ServiceReferenceORM.code,
                    isouter=True
                )
                .join(
                    CountryReferenceORM,
                    subquery.c.country_code == CountryReferenceORM.code,
                    isouter=True
                )
                .where(subquery.c.min_price > 0)
                .order_by(ServiceReferenceORM.name)
            )

            result = await self.session.execute(query)
            rows = result.all()

            services = []
            for row in rows:
                services.append(ServicePrice(
                    service_code=row.service_code,
                    country_code=row.country_code,
                    price=Decimal(str(row.price)) if row.price else Decimal('0.0'),
                    vip_price=float(row.vip_price) if row.vip_price else None,
                    available=bool(row.available),
                    service_name=row.service_name or row.service_code,
                    country_name=row.country_name or country_code
                ))

            self.logger.info(f"Found {len(services)} services for country {country_code}")
            return services

        except Exception as e:
            self.logger.error(f"Error getting services for country {country_code}: {e}")
            raise

    async def get_countries_by_service(self, service_code: str) -> List[ServicePrice]:
        try:
            if os.environ.get("TESTING") == "1":
                # SQLite-совместимая версия
                is_available_expr = func.MAX(
                    case(
                        (
                            and_(
                                ProviderRoutesORM.is_active == True,
                                ProviderRoutesORM.available_count > 0
                            ),
                            1
                        ),
                        else_=0
                    )
                ).label('is_available')
            else:
                # PostgreSQL версия
                is_available_expr = func.bool_or(
                    and_(
                        ProviderRoutesORM.is_active == True,
                        ProviderRoutesORM.available_count > 0
                    )
                ).label('is_available')

            subquery = (
                select(
                    ProviderRoutesORM.service_code,
                    ProviderRoutesORM.country_code,
                    func.min(ProviderRoutesORM.client_price).label('min_price'),
                    func.min(ProviderRoutesORM.vip_client_price).label('min_vip_price'),
                    func.max(ProviderRoutesORM.available_count).label('max_available'),
                    is_available_expr
                )
                .where(ProviderRoutesORM.is_active == True)
                .group_by(
                    ProviderRoutesORM.service_code,
                    ProviderRoutesORM.country_code
                )
                .subquery()
            )

            query = (
                select(
                    subquery.c.service_code,
                    subquery.c.country_code,
                    subquery.c.min_price.label('price'),
                    subquery.c.min_vip_price.label('vip_price'),
                    subquery.c.is_available.label('available'),
                    ServiceReferenceORM.name.label('service_name'),
                    CountryReferenceORM.name_ru.label('country_name')
                )
                .select_from(subquery)
                .join(
                    ServiceReferenceORM,
                    subquery.c.service_code == ServiceReferenceORM.code,
                    isouter=True
                )
                .join(
                    CountryReferenceORM,
                    subquery.c.country_code == CountryReferenceORM.code,
                    isouter=True
                )
                .where(subquery.c.min_price > 0)
                .order_by(CountryReferenceORM.name_ru)
            )

            result = await self.session.execute(query)
            rows = result.all()

            countries = []
            for row in rows:
                countries.append(ServicePrice(
                    service_code=row.service_code,
                    country_code=row.country_code,
                    price=Decimal(str(row.price)) if row.price else Decimal('0.0'),
                    vip_price=float(row.vip_price) if row.vip_price else None,
                    available=bool(row.available),
                    service_name=row.service_name or service_code,
                    country_name=row.country_name or row.country_code
                ))

            self.logger.info(f"Found {len(countries)} countries for service {service_code}")
            return countries

        except Exception as e:
            self.logger.error(f"Error getting countries for service {service_code}: {e}")
            raise

    async def get_popular_services(self) -> List[ServicePrice]:
        try:
            if os.environ.get("TESTING") == "1":
                # SQLite-совместимая версия
                is_available_expr = func.MAX(
                    case(
                        (
                            and_(
                                ProviderRoutesORM.is_active == True,
                                ProviderRoutesORM.available_count > 0
                            ),
                            1
                        ),
                        else_=0
                    )
                ).label('is_available')
            else:
                # PostgreSQL версия
                is_available_expr = func.bool_or(
                    and_(
                        ProviderRoutesORM.is_active == True,
                        ProviderRoutesORM.available_count > 0
                    )
                ).label('is_available')

            subquery = (
                select(
                    ProviderRoutesORM.service_code,
                    ProviderRoutesORM.country_code,
                    func.min(ProviderRoutesORM.client_price).label('min_price'),
                    func.min(ProviderRoutesORM.vip_client_price).label('min_vip_price'),
                    func.max(ProviderRoutesORM.available_count).label('max_available'),
                    is_available_expr
                )
                .where(ProviderRoutesORM.is_active == True)
                .group_by(
                    ProviderRoutesORM.service_code,
                    ProviderRoutesORM.country_code
                )
                .subquery()
            )

            query = (
                select(
                    subquery.c.service_code,
                    subquery.c.country_code,
                    subquery.c.min_price.label('price'),
                    subquery.c.min_vip_price.label('vip_price'),
                    subquery.c.is_available.label('available'),
                    ServiceReferenceORM.name.label('service_name'),
                    CountryReferenceORM.name_ru.label('country_name')
                )
                .select_from(subquery)
                .join(
                    ServiceReferenceORM,
                    and_(
                        subquery.c.service_code == ServiceReferenceORM.code,
                        ServiceReferenceORM.is_popular == True
                    ),
                    isouter=True
                )
                .join(
                    CountryReferenceORM,
                    subquery.c.country_code == CountryReferenceORM.code,
                    isouter=True
                )
                .where(
                    and_(
                        subquery.c.min_price > 0,
                        ServiceReferenceORM.is_popular == True
                    )
                )
                .order_by(ServiceReferenceORM.name)
            )

            result = await self.session.execute(query)
            rows = result.all()

            popular_services = []
            for row in rows:
                popular_services.append(ServicePrice(
                    service_code=row.service_code,
                    country_code=row.country_code,
                    price=Decimal(str(row.price)) if row.price else Decimal('0.0'),
                    vip_price=float(row.vip_price) if row.vip_price else None,
                    available=bool(row.available),
                    service_name=row.service_name or row.service_code,
                    country_name=row.country_name or row.country_code
                ))

            self.logger.info(f"Found {len(popular_services)} popular services")
            return popular_services

        except Exception as e:
            self.logger.error(f"Error getting popular services: {e}")
            raise

    async def get_popular_countries(self) -> List[ServicePrice]:
        try:
            if os.environ.get("TESTING") == "1":
                # SQLite-совместимая версия
                is_available_expr = func.MAX(
                    case(
                        (
                            and_(
                                ProviderRoutesORM.is_active == True,
                                ProviderRoutesORM.available_count > 0
                            ),
                            1
                        ),
                        else_=0
                    )
                ).label('is_available')
            else:
                # PostgreSQL версия
                is_available_expr = func.bool_or(
                    and_(
                        ProviderRoutesORM.is_active == True,
                        ProviderRoutesORM.available_count > 0
                    )
                ).label('is_available')

            subquery = (
                select(
                    ProviderRoutesORM.service_code,
                    ProviderRoutesORM.country_code,
                    func.min(ProviderRoutesORM.client_price).label('min_price'),
                    func.min(ProviderRoutesORM.vip_client_price).label('min_vip_price'),
                    func.max(ProviderRoutesORM.available_count).label('max_available'),
                    is_available_expr
                )
                .where(ProviderRoutesORM.is_active == True)
                .group_by(
                    ProviderRoutesORM.service_code,
                    ProviderRoutesORM.country_code
                )
                .subquery()
            )

            query = (
                select(
                    subquery.c.service_code,
                    subquery.c.country_code,
                    subquery.c.min_price.label('price'),
                    subquery.c.min_vip_price.label('vip_price'),
                    subquery.c.is_available.label('available'),
                    ServiceReferenceORM.name.label('service_name'),
                    CountryReferenceORM.name_ru.label('country_name')
                )
                .select_from(subquery)
                .join(
                    ServiceReferenceORM,
                    subquery.c.service_code == ServiceReferenceORM.code,
                    isouter=True
                )
                .join(
                    CountryReferenceORM,
                    and_(
                        subquery.c.country_code == CountryReferenceORM.code,
                        CountryReferenceORM.is_popular == True
                    ),
                    isouter=True
                )
                .where(
                    and_(
                        subquery.c.min_price > 0,
                        CountryReferenceORM.is_popular == True
                    )
                )
                .order_by(CountryReferenceORM.name_ru)
            )

            result = await self.session.execute(query)
            rows = result.all()

            popular_countries = []
            for row in rows:
                popular_countries.append(ServicePrice(
                    service_code=row.service_code,
                    country_code=row.country_code,
                    price=Decimal(str(row.price)) if row.price else Decimal('0.0'),
                    vip_price=float(row.vip_price) if row.vip_price else None,
                    available=bool(row.available),
                    service_name=row.service_name or row.service_code,
                    country_name=row.country_name or row.country_code
                ))

            self.logger.info(f"Found {len(popular_countries)} popular countries")
            return popular_countries

        except Exception as e:
            self.logger.error(f"Error getting popular countries: {e}")
            raise

    async def get_available_services_countries(self) -> Dict[str, Any]:
        """
        Получить статистику по доступным сервисам и странам
        """
        try:
            # Получаем уникальные комбинации
            query = (
                select(
                    ProviderRoutesORM.service_code,
                    ProviderRoutesORM.country_code,
                    ServiceReferenceORM.name.label('service_name'),
                    CountryReferenceORM.name_ru.label('country_name')
                )
                .distinct()
                .join(
                    ServiceReferenceORM,
                    ProviderRoutesORM.service_code == ServiceReferenceORM.code,
                    isouter=True
                )
                .join(
                    CountryReferenceORM,
                    ProviderRoutesORM.country_code == CountryReferenceORM.code,
                    isouter=True
                )
                .where(
                    and_(
                        ProviderRoutesORM.is_active == True,
                        ProviderRoutesORM.available_count > 0,
                        ProviderRoutesORM.client_price > 0
                    )
                )
            )

            result = await self.session.execute(query)
            rows = result.all()

            services_count = len(set(row.service_code for row in rows))
            countries_count = len(set(row.country_code for row in rows))
            combinations_count = len(rows)

            return {
                "total_services": services_count,
                "total_countries": countries_count,
                "total_combinations": combinations_count,
                "services": list(set(row.service_code for row in rows)),
                "countries": list(set(row.country_code for row in rows))
            }

        except Exception as e:
            self.logger.error(f"Error getting available services/countries: {e}")
            raise

    async def get_detailed_prices_for_service_country(self, service_code: str, country_code: str) -> List[Any]:
        try:
            query = (
                select(
                    ProviderRoutesORM.service_code,
                    ProviderRoutesORM.country_code,
                    ProviderRoutesORM.client_price.label('price'),
                    ProviderRoutesORM.vip_client_price.label('vip_price'),
                    ProviderRoutesORM.available_count > 0,
                    ProviderRoutesORM.provider_id,
                    ProviderORM.name.label('provider_name'),
                    ProviderRoutesORM.rating_score,
                    ProviderRoutesORM.success_rate,
                    ServiceReferenceORM.name.label('service_name'),
                    CountryReferenceORM.name_ru.label('country_name')
                )
                .select_from(ProviderRoutesORM)
                .join(ProviderORM, ProviderRoutesORM.provider_id == ProviderORM.id)
                .join(ServiceReferenceORM, ProviderRoutesORM.service_code == ServiceReferenceORM.code, isouter=True)
                .join(CountryReferenceORM, ProviderRoutesORM.country_code == CountryReferenceORM.code, isouter=True)
                .where(
                    and_(
                        ProviderRoutesORM.service_code == service_code,
                        ProviderRoutesORM.country_code == country_code,
                        ProviderRoutesORM.is_active == True,
                        ProviderRoutesORM.client_price > 0
                    )
                )
                .order_by(ProviderRoutesORM.client_price.asc())
            )

            result = await self.session.execute(query)
            return result.all()

        except Exception as e:
            self.logger.error(f"Error getting detailed prices for {service_code}/{country_code}: {e}")
            raise
