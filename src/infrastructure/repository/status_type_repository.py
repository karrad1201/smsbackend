from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Any

from src.core.domain.repository.interfaces import IStatusTypeRepository
from src.core.domain.entity.status_type import StatusType
from src.infrastructure.database.schemas import StatusTypeORM
from src.core.logging_config import get_logger


class StatusTypeRepository(IStatusTypeRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = get_logger(__name__)

    async def get_by_code(self, code: str) -> Optional[StatusType]:
        try:
            result = await self.session.execute(
                select(StatusTypeORM).where(StatusTypeORM.code == code)
            )
            status_orm = result.scalar_one_or_none()

            if not status_orm:
                return None

            return self._orm_to_entity(status_orm)
        except Exception as e:
            self.logger.error(f"Error getting status type by code {code}: {e}")
            raise

    async def get_final_statuses(self) -> List[Any]:
        try:
            result = await self.session.execute(
                select(StatusTypeORM).where(StatusTypeORM.is_final == True)
            )
            statuses_orm = result.scalars().all()

            return [self._orm_to_entity(status_orm) for status_orm in statuses_orm]
        except Exception as e:
            self.logger.error(f"Error getting final statuses: {e}")
            raise

    async def get_error_statuses(self) -> List[Any]:
        try:
            result = await self.session.execute(
                select(StatusTypeORM).where(StatusTypeORM.is_error == True)
            )
            statuses_orm = result.scalars().all()

            return [self._orm_to_entity(status_orm) for status_orm in statuses_orm]
        except Exception as e:
            self.logger.error(f"Error getting error statuses: {e}")
            raise

    def _orm_to_entity(self, status_orm: StatusTypeORM) -> StatusType:
        return StatusType(
            id=status_orm.id,
            code=status_orm.code,
            name_ru=status_orm.name_ru,
            name_en=status_orm.name_en,
            is_final=status_orm.is_final,
            is_error=status_orm.is_error,
            description=status_orm.description
        )
