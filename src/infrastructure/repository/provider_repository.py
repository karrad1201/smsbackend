from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from src.core.domain.repository.interfaces import IProviderRepository
from src.core.domain.entity.provider import Provider
from src.infrastructure.database.schemas import ProviderORM
from src.core.logging_config import get_logger


class ProviderRepository(IProviderRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = get_logger(__name__)

    async def get_by_name(self, name: str) -> Optional[Provider]:
        try:
            result = await self.session.execute(
                select(ProviderORM).where(ProviderORM.name == name)
            )
            provider_orm = result.scalar_one_or_none()

            if not provider_orm:
                return None

            return self._orm_to_entity(provider_orm)
        except Exception as e:
            self.logger.error(f"Error getting provider by name {name}: {e}")
            raise

    async def get_active_providers(self) -> List[Provider]:
        try:
            result = await self.session.execute(
                select(ProviderORM)
                .where(ProviderORM.is_active == True)
                .order_by(ProviderORM.priority.desc(), ProviderORM.name)
            )
            providers_orm = result.scalars().all()

            return [self._orm_to_entity(provider_orm) for provider_orm in providers_orm]
        except Exception as e:
            self.logger.error(f"Error getting active providers: {e}")
            raise

    def _orm_to_entity(self, provider_orm: ProviderORM) -> Provider:
        return Provider(
            id=provider_orm.id,
            name=provider_orm.name,
            adapter_class=provider_orm.adapter_class,
            config=provider_orm.config,
            is_active=provider_orm.is_active,
            display_name=provider_orm.display_name,
            api_url=provider_orm.api_url,
            priority=provider_orm.priority,
            max_requests_per_second=provider_orm.max_requests_per_second,
            timeout_seconds=provider_orm.timeout_seconds,
            adapter_type=provider_orm.adapter_type,
            mapping_type=provider_orm.mapping_type,
            max_requests_per_minute=provider_orm.max_requests_per_minute,
            created_at=provider_orm.created_at,
            updated_at=provider_orm.updated_at
        )
