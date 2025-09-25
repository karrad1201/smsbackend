from src.services.user_service import UserService
from src.services.haser_service import HasherService
from src.services.JWT_service import JWTService
from src.core.di.repository import get_user_repo
from src.services.heleket_service import HeleketService
from src.services.payment_service import PaymentService
from src.core.di.repository import get_payment_repo
from fastapi import Depends


def get_user_service(user_repo=Depends(get_user_repo)) -> UserService:
    return UserService(user_repo=user_repo)


def get_hasher_service() -> HasherService:
    return HasherService()


def get_jwt_service() -> JWTService:
    return JWTService()

def get_heleket_service() -> HeleketService:
    return HeleketService()

def get_payment_service(payment_repo=Depends(get_payment_repo)) -> PaymentService:
    return PaymentService(payment_repo)

__all__ = [
    "get_user_service",
    "get_hasher_service",
    "get_jwt_service",
    "get_heleket_service",
    "get_payment_service"
]