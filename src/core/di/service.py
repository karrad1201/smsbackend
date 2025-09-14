from src.services.user_service import UserService
from src.core.di.repository import get_user_repo
from fastapi import Depends

def get_user_service(user_repo = Depends(get_user_repo)) -> UserService:
    return UserService(user_repo=user_repo)