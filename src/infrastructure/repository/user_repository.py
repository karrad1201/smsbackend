from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from typing import List, Optional
from datetime import datetime

from src.core.domain.repository.interfaces import IUserRepository
from src.core.domain.entity.user import User, UserCreate
from src.infrastructure.database.schemas import UserORM
from src.core.exceptions.exceptions import AlreadyExistsException, NotFoundException
from src.core.logging_config import get_logger


class UserRepository(IUserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = get_logger(__name__)

    async def get_by_id(self, id: int) -> Optional[User]:
        try:
            result = await self.session.execute(
                select(UserORM).where(UserORM.id == id)
            )
            user_orm = result.scalar_one_or_none()

            if not user_orm:
                return None

            return self._orm_to_entity(user_orm)
        except Exception as e:
            self.logger.error(f"Error getting user by id {id}: {e}")
            raise

    async def get_by_username(self, username: str) -> Optional[User]:
        try:
            result = await self.session.execute(
                select(UserORM).where(UserORM.user_name == username)
            )
            user_orm = result.scalar_one_or_none()

            if not user_orm:
                return None

            return self._orm_to_entity(user_orm)
        except Exception as e:
            self.logger.error(f"Error getting user by username {username}: {e}")
            raise

    async def get_by_email(self, email: str) -> Optional[User]:
        try:
            result = await self.session.execute(
                select(UserORM).where(UserORM.email == email)
            )
            user_orm = result.scalar_one_or_none()

            if not user_orm:
                return None

            return self._orm_to_entity(user_orm)
        except Exception as e:
            self.logger.error(f"Error getting user by email {email}: {e}")
            raise

    async def get_by_api_key(self, api_key: str) -> Optional[User]:
        try:
            result = await self.session.execute(
                select(UserORM).where(UserORM.api_key == api_key)
            )
            user_orm = result.scalar_one_or_none()

            if not user_orm:
                return None

            return self._orm_to_entity(user_orm)
        except Exception as e:
            self.logger.error(f"Error getting user by API key: {e}")
            raise

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        try:
            result = await self.session.execute(
                select(UserORM)
                .offset(skip)
                .limit(limit)
                .order_by(UserORM.id)
            )
            users_orm = result.scalars().all()

            return [self._orm_to_entity(user_orm) for user_orm in users_orm]
        except Exception as e:
            self.logger.error(f"Error getting all users: {e}")
            raise

    async def create(self, user_create: UserCreate) -> User:
        try:
            if await self.get_by_username(user_create.user_name):
                self.logger.error(f"User with username {user_create.user_name} already exists")
                raise AlreadyExistsException

            if user_create.email and await self.get_by_email(user_create.email):
                self.logger.error(f"User with username {user_create.user_name} already exists")
                raise AlreadyExistsException

            user_orm = UserORM(
                user_name=user_create.user_name,
                first_name=user_create.first_name,
                last_name=user_create.last_name,
                email=user_create.email,
                password_hash=user_create.password,
                balance=0.0,
                discount_rate=0.0,
                is_admin=False,
                language=None,
                api_key=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.session.add(user_orm)
            await self.session.commit()
            await self.session.refresh(user_orm)

            return self._orm_to_entity(user_orm)
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Error creating user: {e}")
            raise

    async def update(self, user: User) -> Optional[User]:
        try:
            existing_user = await self.get_by_id(user.id)
            if not existing_user:
                self.logger.error(f"User with id {user.id} not found")
                raise NotFoundException

            if user.email and user.email != existing_user.email:
                if await self.get_by_email(user.email):
                    self.logger.error(f"User with email {user.email} already exists")
                    raise AlreadyExistsException

            update_data = {
                "first_name": user.first_name,
                "user_name": user.user_name,
                "last_name": user.last_name,
                "email": user.email,
                "language": user.language,
                "discount_rate": user.discount_rate,
                "updated_at": datetime.utcnow()
            }

            result = await self.session.execute(
                update(UserORM)
                .where(UserORM.id == user.id)
                .values(**update_data)
                .returning(UserORM)
            )

            user_orm = result.scalar_one_or_none()
            if not user_orm:
                return None

            await self.session.commit()
            return self._orm_to_entity(user_orm)
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Error updating user {user.id}: {e}")
            raise

    async def update_balance(self, user_id: int, amount: float) -> Optional[User]:
        try:
            result = await self.session.execute(
                update(UserORM)
                .where(UserORM.id == user_id)
                .values(
                    balance=UserORM.balance + amount,
                    updated_at=datetime.utcnow()
                )
                .returning(UserORM)
            )

            user_orm = result.scalar_one_or_none()
            if not user_orm:
                return None

            await self.session.commit()
            return self._orm_to_entity(user_orm)
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Error updating balance for user {user_id}: {e}")
            raise

    async def update_password(self, user_id: int, password_hash: str) -> bool:
        try:
            result = await self.session.execute(
                update(UserORM)
                .where(UserORM.id == user_id)
                .values(
                    password_hash=password_hash,
                    updated_at=datetime.utcnow()
                )
            )

            await self.session.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Error updating password for user {user_id}: {e}")
            raise

    async def update_api_key(self, user_id: int, api_key: str) -> bool:
        try:
            result = await self.session.execute(
                update(UserORM)
                .where(UserORM.id == user_id)
                .values(
                    api_key=api_key,
                    updated_at=datetime.utcnow()
                )
            )

            await self.session.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Error updating API key for user {user_id}: {e}")
            raise

    async def delete(self, id: int) -> bool:
        try:
            result = await self.session.execute(
                select(UserORM).where(UserORM.id == id)
            )
            user_orm = result.scalar_one_or_none()

            if not user_orm:
                return False

            await self.session.delete(user_orm)
            await self.session.commit()
            return True
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Error deleting user {id}: {e}")
            raise

    async def user_exists(self, username: str, email: str = None) -> bool:
        try:
            conditions = [UserORM.user_name == username]
            if email:
                conditions.append(UserORM.email == email)

            result = await self.session.execute(
                select(UserORM.id).where(and_(*conditions))
            )
            return result.scalar_one_or_none() is not None
        except Exception as e:
            self.logger.error(f"Error checking user existence: {e}")
            raise

    async def get_password_hash(self, user_id: int) -> str:
        try:
            result = await self.session.execute(
                select(UserORM.password_hash).where(UserORM.id == user_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            self.logger.error(f"Error getting password hash for user {user_id}: {e}")
            raise

    def _orm_to_entity(self, user_orm: UserORM) -> User:
        return User(
            id=user_orm.id,
            user_name=user_orm.user_name,
            first_name=user_orm.first_name,
            last_name=user_orm.last_name,
            email=user_orm.email,
            balance=float(user_orm.balance),
            language=user_orm.language,
            discount_rate=float(user_orm.discount_rate),
            is_admin=user_orm.is_admin,
            created_at=user_orm.created_at,
            updated_at=user_orm.updated_at
        )
