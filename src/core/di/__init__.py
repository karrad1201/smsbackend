from src.core.di.service import *
from src.core.di.repository import *
from src.core.domain.entity.user import User
from fastapi import Depends, HTTPException, Header
from src.services.user_service import UserService
from src.services.JWT_service import JWTService
from src.core.logging_config import get_logger

logger = get_logger(__name__)


async def get_current_user(
        authorization: str = Header(None, alias="Authorization"),
        user_service: UserService = Depends(get_user_service),
        jwt_service: JWTService = Depends(get_jwt_service),
) -> User:
    try:
        logger.info("Starting user authentication")

        if not authorization:
            logger.error("No authorization header provided")
            raise HTTPException(status_code=401, detail="Authorization header required")

        if not authorization.startswith("Bearer "):
            logger.error(f"Invalid authorization format: {authorization}")
            raise HTTPException(status_code=401, detail="Invalid authorization header format")

        token = authorization[7:]
        logger.info(f"Token extracted, length: {len(token)}")

        # Проверяем токен перед извлечением user_id
        if not jwt_service.verify_token(token):
            logger.error("Token verification failed")
            raise HTTPException(status_code=401, detail="Invalid token")

        user_id = jwt_service.get_user_id_from_token(token)
        logger.info(f"Extracted user_id: {user_id}")

        if not user_id:
            logger.error("Failed to extract user_id from token")
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await user_service.get_by_id(user_id)
        if not user:
            logger.error(f"User with id {user_id} not found")
            raise HTTPException(status_code=404, detail="User not found")

        logger.info(f"User authenticated: {user.user_name} (ID: {user.id})")
        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_current_user: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")