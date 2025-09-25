from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional

from src.core.domain.repository.interfaces import IServiceRepository
from src.core.domain.entity.services import ServicePublic
from src.infrastructure.database.schemas import ServiceReferenceORM
from src.core.logging_config import get_logger


class ServiceRepository(IServiceRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = get_logger(__name__)

    async def get_by_id(self, id: int) -> Optional[ServicePublic]:
        try:
            result = await self.session.execute(
                select(ServiceReferenceORM).where(ServiceReferenceORM.id == id)
            )
            service_orm = result.scalar_one_or_none()
            return self._orm_to_entity(service_orm) if service_orm else None
        except Exception as e:
            self.logger.error(f"Error getting service by id {id}: {e}")
            raise

    async def get_by_code(self, code: str) -> Optional[ServicePublic]:
        try:
            result = await self.session.execute(
                select(ServiceReferenceORM).where(ServiceReferenceORM.code == code)
            )
            service_orm = result.scalar_one_or_none()
            return self._orm_to_entity(service_orm) if service_orm else None
        except Exception as e:
            self.logger.error(f"Error getting service by code {code}: {e}")
            raise

    async def get_popular_services(self) -> List[ServicePublic]:
        try:
            result = await self.session.execute(
                select(ServiceReferenceORM)
                .where(and_(
                    ServiceReferenceORM.is_popular == True,
                    ServiceReferenceORM.is_active == True
                ))
                .order_by(ServiceReferenceORM.sort_order, ServiceReferenceORM.name)
            )
            services_orm = result.scalars().all()
            return [self._orm_to_entity(service) for service in services_orm]
        except Exception as e:
            self.logger.error(f"Error getting popular services: {e}")
            raise

    async def get_services_by_category(self, category: str) -> List[ServicePublic]:
        try:
            result = await self.session.execute(
                select(ServiceReferenceORM)
                .where(and_(
                    ServiceReferenceORM.category == category,
                    ServiceReferenceORM.is_active == True
                ))
                .order_by(ServiceReferenceORM.sort_order, ServiceReferenceORM.name)
            )
            services_orm = result.scalars().all()
            return [self._orm_to_entity(service) for service in services_orm]
        except Exception as e:
            self.logger.error(f"Error getting services by category {category}: {e}")
            raise

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ServicePublic]:
        try:
            result = await self.session.execute(
                select(ServiceReferenceORM)
                .where(ServiceReferenceORM.is_active == True)
                .order_by(ServiceReferenceORM.sort_order, ServiceReferenceORM.name)
                .offset(skip)
                .limit(limit)
            )
            services_orm = result.scalars().all()
            return [self._orm_to_entity(service) for service in services_orm]
        except Exception as e:
            self.logger.error(f"Error getting all services: {e}")
            raise

    def _orm_to_entity(self, service_orm: ServiceReferenceORM) -> ServicePublic:
        return ServicePublic(
            code=service_orm.code,
            name=service_orm.name,
            category=service_orm.category,
            icon=service_orm.icon,
            is_popular=service_orm.is_popular,
            description=service_orm.description
        )