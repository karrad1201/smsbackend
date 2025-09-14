from abc import ABC, abstractmethod
from src.core.domain.entity.user import User

class IUserRepository(ABC):
    @abstractmethod
    async def get_all(self) -> list[User]:
        pass