from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func
from typing import List, Optional

from src.core.domain.repository.interfaces import IProviderRouteRepository
from src.core.domain.entity.provider_route import ProviderRoute, BestProviderPrice
from src.infrastructure.database.schemas import ProviderRoutesORM, ProviderORM
from src.core.logging_config import get_logger


class ProviderRouteRepository(IProviderRouteRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = get_logger(__name__)

    async def get_by_id(self, id: int) -> Optional[ProviderRoute]:
        try:
            result = await self.session.execute(
                select(ProviderRoutesORM).where(ProviderRoutesORM.id == id)
            )
            route_orm = result.scalar_one_or_none()

            if not route_orm:
                return None

            return self._orm_to_entity(route_orm)
        except Exception as e:
            self.logger.error(f"Error getting provider route by id {id}: {e}")
            raise

    async def get_best_price_for_service_country(self, service_code: str, country_code: str) -> Optional[
        BestProviderPrice]:
        try:
            query = (
                select(
                    ProviderRoutesORM,
                    ProviderORM.name.label('provider_name')
                )
                .join(ProviderORM, ProviderRoutesORM.provider_id == ProviderORM.id)
                .where(
                    and_(
                        ProviderRoutesORM.service_code == service_code,
                        ProviderRoutesORM.country_code == country_code,
                        ProviderRoutesORM.is_active == True,
                        ProviderRoutesORM.available_count > 0,
                        ProviderRoutesORM.client_price > 0
                    )
                )
                .order_by(
                    ProviderRoutesORM.client_price.asc(),
                    ProviderRoutesORM.rating_score.desc(),
                    ProviderRoutesORM.success_rate.desc()
                )
                .limit(1)
            )

            result = await self.session.execute(query)
            row = result.first()

            if not row:
                return None

            route_orm = row[0]
            provider_name = row[1]

            return BestProviderPrice(
                service_code=route_orm.service_code,
                country_code=route_orm.country_code,
                price=route_orm.client_price,
                vip_price=route_orm.vip_client_price,
                provider_id=route_orm.provider_id,
                provider_name=provider_name,
                available=route_orm.available_count > 0,
                rating=float(route_orm.rating_score)
            )
        except Exception as e:
            self.logger.error(f"Error getting best price for {service_code}/{country_code}: {e}")
            raise

    async def get_prices_for_service_country(self, service_code: str, country_code: str) -> List[BestProviderPrice]:
        try:
            query = (
                select(
                    ProviderRoutesORM,
                    ProviderORM.name.label('provider_name')
                )
                .join(ProviderORM, ProviderRoutesORM.provider_id == ProviderORM.id)
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
            rows = result.all()

            prices = []
            for row in rows:
                route_orm = row[0]
                provider_name = row[1]

                prices.append(BestProviderPrice(
                    service_code=route_orm.service_code,
                    country_code=route_orm.country_code,
                    price=route_orm.client_price,
                    vip_price=route_orm.vip_client_price,
                    provider_id=route_orm.provider_id,
                    provider_name=provider_name,
                    available=route_orm.available_count > 0,
                    rating=float(route_orm.rating_score)
                ))

            return prices
        except Exception as e:
            self.logger.error(f"Error getting prices for {service_code}/{country_code}: {e}")
            raise

    async def update_route_stats(self, route_id: int, success: bool, response_time_ms: int) -> bool:
        try:
            route = await self.get_by_id(route_id)
            if not route:
                return False

            update_data = {
                "total_attempts": ProviderRoutesORM.total_attempts + 1,
                "avg_response_time_ms": func.round(
                    (ProviderRoutesORM.avg_response_time_ms * ProviderRoutesORM.total_attempts + response_time_ms) /
                    (ProviderRoutesORM.total_attempts + 1)
                ),
                "updated_at": func.now()
            }

            if success:
                update_data["successful_attempts"] = ProviderRoutesORM.successful_attempts + 1
                update_data["consecutive_failures"] = 0
                update_data["last_success_at"] = func.now()
                update_data["success_rate"] = func.round(
                    (ProviderRoutesORM.successful_attempts + 1) * 100.0 / (ProviderRoutesORM.total_attempts + 1),
                    2
                )
            else:
                update_data["consecutive_failures"] = ProviderRoutesORM.consecutive_failures + 1
                update_data["last_failure_at"] = func.now()
                update_data["success_rate"] = func.round(
                    ProviderRoutesORM.successful_attempts * 100.0 / (ProviderRoutesORM.total_attempts + 1),
                    2
                )

            success_rate = update_data.get("success_rate", route.success_rate)
            if success_rate > 95:
                rating_increase = 2
            elif success_rate > 80:
                rating_increase = 1
            elif success_rate < 50:
                rating_increase = -2
            elif success_rate < 70:
                rating_increase = -1
            else:
                rating_increase = 0

            update_data["rating_score"] = func.greatest(
                0, func.least(100, ProviderRoutesORM.rating_score + rating_increase)
            )

            result = await self.session.execute(
                update(ProviderRoutesORM)
                .where(ProviderRoutesORM.id == route_id)
                .values(**update_data)
            )

            await self.session.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Error updating stats for route {route_id}: {e}")
            raise

    async def get_active_routes_for_provider(self, provider_id: int) -> List[ProviderRoute]:
        try:
            result = await self.session.execute(
                select(ProviderRoutesORM)
                .where(
                    and_(
                        ProviderRoutesORM.provider_id == provider_id,
                        ProviderRoutesORM.is_active == True
                    )
                )
                .order_by(ProviderRoutesORM.service_code, ProviderRoutesORM.country_code)
            )
            routes_orm = result.scalars().all()

            return [self._orm_to_entity(route_orm) for route_orm in routes_orm]
        except Exception as e:
            self.logger.error(f"Error getting active routes for provider {provider_id}: {e}")
            raise

    def _orm_to_entity(self, route_orm: ProviderRoutesORM) -> ProviderRoute:
        return ProviderRoute(
            id=route_orm.id,
            provider_id=route_orm.provider_id,
            country_code=route_orm.country_code,
            service_code=route_orm.service_code,
            provider_country_code=route_orm.provider_country_code,
            provider_service_code=route_orm.provider_service_code,
            cost_price=route_orm.cost_price,
            client_price=route_orm.client_price,
            vip_client_price=route_orm.vip_client_price,
            min_margin_percent=route_orm.min_margin_percent,
            available_count=route_orm.available_count,
            max_daily_limit=route_orm.max_daily_limit,
            priority=route_orm.priority,
            rating_score=float(route_orm.rating_score),
            success_rate=float(route_orm.success_rate),
            is_active=route_orm.is_active,
            created_at=route_orm.created_at,
            updated_at=route_orm.updated_at
        )
