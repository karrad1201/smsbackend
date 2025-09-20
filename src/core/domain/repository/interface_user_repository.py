from abc import ABC, abstractmethod
from src.core.domain.entity.user import UserPublic

class IUserRepository(ABC):
    @abstractmethod
    async def get_all(self) -> list[UserPublic]:
        pass