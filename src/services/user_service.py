from src.core.domain.repository.interface_user_repository import IUserRepository

class UserService:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    async def get_users(self):
        return await self.user_repo.get_all()