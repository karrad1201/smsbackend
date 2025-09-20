from fastapi import APIRouter, Depends
from src.core.di import get_user_service

user_router = APIRouter(prefix="/user")


@user_router.get("/users")
async def get_users(user_service=Depends(get_user_service)):
    return await user_service.get_users()
