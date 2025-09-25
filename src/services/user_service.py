from src.core.domain.repository.interfaces import IUserRepository
from src.services.haser_service import HasherService
from src.core.domain.entity.user import User
from src.core.domain.mappers.user_mapper import UserMapper
from src.core.domain.dto.user_dto import UserCreateDTO, UserProfileDTO
from src.core.exceptions.exceptions import AlreadyExistsException
from typing import Optional


class UserService:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo
        self.hasher_service = HasherService()
        self.user_mapper = UserMapper()

    async def get_all_users(self) -> list[UserProfileDTO]:
        users = await self.user_repo.get_all()
        return [self.user_mapper.entity_to_profile_dto(user) for user in users]

    async def get_by_id(self, id: int) -> Optional[User]:
        return await self.user_repo.get_by_id(id=id)

    async def get_by_username(self, username: str) -> Optional[User]:
        return await self.user_repo.get_by_username(username=username)

    async def get_by_email(self, email: str) -> Optional[User]:
        return await self.user_repo.get_by_email(email=email)

    async def get_by_api_key(self, api_key: str) -> Optional[User]:
        return await self.user_repo.get_by_api_key(api_key=api_key)

    async def register_user(self, user_dto: UserCreateDTO) -> Optional[UserProfileDTO]:
        existing_user = await self.user_repo.get_by_username(user_dto.user_name)
        if existing_user:
            raise AlreadyExistsException

        user_entity = self.user_mapper.create_dto_to_entity(user_dto)
        hashed_password = self.hasher_service.hash(user_dto.password)
        user_entity.password = hashed_password

        user = await self.user_repo.create(user_entity)
        return self.user_mapper.entity_to_profile_dto(user)

    async def update_user(self, user: User) -> Optional[User]:
        return await self.user_repo.update(user)

    async def update_password(self, user_id: int, password: str):
        hashed_password = self.hasher_service.hash(password)
        return await self.user_repo.update_password(user_id, hashed_password)

    async def update_balance(self, user_id: int, amount: int):
        return await self.user_repo.update_balance(user_id, amount)

    async def update_api_key(self, user_id: int, api_key: str):
        return await self.user_repo.update_api_key(user_id, api_key)

    async def delete_user(self, user_id: int):
        return await self.user_repo.delete(user_id)

    async def check_user_exists(self, user_id: int) -> bool:
        return await self.user_repo.user_exists(user_id)

    async def get_password_hash(self, user_id: int) -> str:
        return await self.user_repo.get_password_hash(user_id)
