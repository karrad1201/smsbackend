from .health import health_router
from src.presentation.webhooks import router as webhooks_router
from src.presentation.api.payments.payment_router import router as payment_router
from .user.user_router import user_router

routers = [
    health_router,
    user_router,
    payment_router,
    webhooks_router
]