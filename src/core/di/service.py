from src.services.user_service import UserService
from src.services.haser_service import HasherService
from src.services.JWT_service import JWTService
from src.core.di.repository import get_user_repo
from src.services.heleket_service import HeleketService
from src.services.payment_service import PaymentService
from src.core.di.repository import get_payment_repo
from src.core.di.repository import get_price_repo
from src.core.di.repository import get_order_repo
from src.services.price_service import PriceService
from src.services.order_service import OrderService
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

def get_price_service(price_repo=Depends(get_price_repo)) -> PriceService:
    return PriceService(price_repo)

def get_order_service(price_repo=Depends(get_price_repo), order_repo=Depends(get_order_repo), user_repo=Depends(get_user_repo)) -> OrderService:
    return OrderService(price_repo=price_repo, order_repo=order_repo, user_repo=user_repo)

__all__ = [
    "get_user_service",
    "get_hasher_service",
    "get_jwt_service",
    "get_heleket_service",
    "get_payment_service",
    "get_price_service",
    "get_order_service"
]