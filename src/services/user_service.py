from src.core.domain.repository.interface_user_repository import IUserRepository
from src.services.haser_service import HasherService
from src.core.domain.entity.user import UserPrivate, UserPublic, UserCreate

class UserService:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo
        self.haser_service = HasherService()

    async def get_users(self) -> list[UserPublic]:
        return await self.user_repo.get_all()

    async def get_by_id(self, id: int) -> UserPublic:
        return await self.user_repo.get_by_id

    async def register_user(self, user: UserCreate) -> int:
        password = user.password
        hashed_password = self.haser_service.hash(password)
        user.password = hashed_password
        return await self.user_repo.create(user)

