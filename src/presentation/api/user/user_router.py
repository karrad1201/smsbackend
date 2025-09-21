from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from src.core.di import get_user_service, get_jwt_service, get_current_user
from src.core.domain.entity.user import UserCreate, UserPublic
from src.core.logging_config import get_logger
from src.core.exceptions.exceptions import AlredyExistsException

user_router = APIRouter(prefix="/user")
logger = get_logger(__name__)

@user_router.get("/users")
async def get_users(user_service=Depends(get_user_service)) -> list[UserPublic]:
    try:
        return await user_service.get_users()
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@user_router.post("/register")
async def register_user(
    user: UserCreate,
    user_service=Depends(get_user_service),
    jwt_service=Depends(get_jwt_service)
):
    try:
        user_id = await user_service.register_user(user)
        token = jwt_service.encode({"user_id": user_id})
        logger.info(f"User {user.name} registered with id {user_id}")
        return {"token": token}
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except AlredyExistsException as e:
        logger.warning(f"User {user.name} already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error registering user {user.name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )