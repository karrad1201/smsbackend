from abc import ABC, abstractmethod
from src.core.domain.entity.user import UserPublic

class IUserRepository(ABC):
    @abstractmethod
    async def get_all(self) -> list[UserPublic]:
        pass

    @abstractmethod
    async def get_by_id(self, id: int) -> UserPublic:
        pass

    @abstractmethod
    async def create(self, user: UserPublic) -> int:
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> UserPublic:
        pass