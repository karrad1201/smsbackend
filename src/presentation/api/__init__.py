from .health import health_router
from .user.user_router import user_router

routers = [
    health_router,
    user_router
]