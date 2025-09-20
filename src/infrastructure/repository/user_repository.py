from src.core.domain.repository.interface_user_repository import IUserRepository
from src.core.domain.entity.user import UserPublic
from src.infrastructure.database.schemas import UserORM
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.core.logging_config import get_logger

class UserRepository(IUserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = get_logger(__name__)

    async def get_all(self, limit: int = 100, offset: int = 0) -> list[UserPublic]:
        result = await self.session.execute(
            select(UserORM)
            .limit(limit)
            .offset(offset)
        )
        users_orm = result.scalars().all()
        return [UserPublic.model_validate(user_orm) for user_orm in users_orm]

    async def to_entity(self, user_orm: UserORM) -> UserPublic:
        return UserPublic(
            id=user_orm.id,
            name=user_orm.name
        )

    async def to_orm(self, user: UserPublic) -> UserORM:
        return UserORM(
            id=user.id,
            name=user.name
        )