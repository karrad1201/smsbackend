from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional

from src.core.domain.repository.interfaces import ICountryRepository
from src.core.domain.entity.countries import CountryPublic
from src.infrastructure.database.schemas import CountryReferenceORM
from src.core.logging_config import get_logger


class CountryRepository(ICountryRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = get_logger(__name__)

    async def get_by_code(self, code: str) -> Optional[CountryPublic]:
        try:
            result = await self.session.execute(
                select(CountryReferenceORM).where(CountryReferenceORM.code == code)
            )
            country_orm = result.scalar_one_or_none()

            if not country_orm:
                return None

            return self._orm_to_entity(country_orm)
        except Exception as e:
            self.logger.error(f"Error getting country by code {code}: {e}")
            raise

    async def get_popular_countries(self) -> List[CountryPublic]:
        try:
            result = await self.session.execute(
                select(CountryReferenceORM)
                .where(
                    and_(
                        CountryReferenceORM.is_popular == True,
                        CountryReferenceORM.is_active == True
                    )
                )
                .order_by(CountryReferenceORM.sort_order, CountryReferenceORM.name_ru)
            )
            countries_orm = result.scalars().all()

            return [self._orm_to_entity(country_orm) for country_orm in countries_orm]
        except Exception as e:
            self.logger.error(f"Error getting popular countries: {e}")
            raise

    async def get_countries_by_region(self, region: str) -> List[CountryPublic]:
        try:
            result = await self.session.execute(
                select(CountryReferenceORM)
                .where(
                    and_(
                        CountryReferenceORM.region == region,
                        CountryReferenceORM.is_active == True
                    )
                )
                .order_by(CountryReferenceORM.name_ru)
            )
            countries_orm = result.scalars().all()

            return [self._orm_to_entity(country_orm) for country_orm in countries_orm]
        except Exception as e:
            self.logger.error(f"Error getting countries by region {region}: {e}")
            raise


    def _orm_to_entity(self, country_orm: CountryReferenceORM) -> CountryPublic:
        return CountryPublic(
            code=country_orm.code,
            name_ru=country_orm.name_ru,
            name_en=country_orm.name_en,
            iso_code=country_orm.iso_code,
            region=country_orm.region,
            is_popular=country_orm.is_popular
        )