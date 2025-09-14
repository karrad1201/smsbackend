from src.core.domain.repository.interface_user_repository import IUserRepository
from src.infrastructure.repository.user_repository import UserRepository
from src.infrastructure.database.connection import get_db_session
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

def get_user_repo(session: AsyncSession = Depends(get_db_session)) -> IUserRepository:
    return UserRepository(session=session)