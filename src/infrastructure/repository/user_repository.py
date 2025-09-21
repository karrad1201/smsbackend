from src.core.domain.repository.interface_user_repository import IUserRepository
from src.core.domain.entity.user import UserPublic, UserCreate, UserBase
from src.infrastructure.database.schemas import UserORM
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.core.logging_config import get_logger
from typing import Optional
from src.core.exceptions.exceptions import AlredyExistsException

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

    async def create(self, user: UserCreate) -> int:
        existing_user = await self.get_by_username(user.name)
        if existing_user:
            raise AlredyExistsException

        user_orm = UserORM(
            name=user.name,
            password_hash=user.password
        )
        self.session.add(user_orm)
        await self.session.commit()
        await self.session.refresh(user_orm)
        return user_orm.id

    async def get_by_id(self, id: int) -> Optional[UserPublic]:
        result = await self.session.execute(
            select(UserORM).where(UserORM.id == id)
        )
        user_orm = result.scalar_one_or_none()
        if user_orm is None:
            return None
        return UserPublic.model_validate(user_orm)

    async def get_by_username(self, username: str) -> Optional[UserPublic]:
        result = await self.session.execute(
            select(UserORM).where(UserORM.name == username)
        )
        user_orm = result.scalar_one_or_none()
        if user_orm is None:
            return None
        return UserPublic.model_validate(user_orm)