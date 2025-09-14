from src.core.domain.repository.interface_user_repository import IUserRepository
from src.core.domain.entity.user import User
from src.infrastructure.database.schemas import UserORM
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.core.logging_config import get_logger

class UserRepository(IUserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = get_logger(__name__)

    async def get_all(self) -> list[User]:
        result = await self.session.execute(select(UserORM))
        users_orm = result.scalars().all()
        return [await self.to_entity(user_orm) for user_orm in users_orm]

    async def to_entity(self, user_orm: UserORM) -> User:
        return User(
            id=user_orm.id,
            name=user_orm.name
        )

    async def to_orm(self, user: User) -> UserORM:
        return UserORM(
            id=user.id,
            name=user.name
        )