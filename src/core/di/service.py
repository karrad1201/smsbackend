from src.services.user_service import UserService
from src.services.haser_service import HasherService
from src.services.JWT_service import JWTService
from src.core.di.repository import get_user_repo
from fastapi import Depends

def get_user_service(user_repo = Depends(get_user_repo)) -> UserService:
    return UserService(user_repo=user_repo)

def get_hasher_service() -> HasherService:
    return HasherService()

def get_jwt_service() -> JWTService:
    return JWTService()