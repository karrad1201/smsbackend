from src.core.di.service import get_user_service, get_hasher_service, get_jwt_service
from src.core.domain.entity.user import UserPublic
from fastapi import Depends
from src.services.user_service import UserService
from src.services.JWT_service import JWTService


async def get_current_user(
        JWT_token: str,
        user_service: UserService = Depends(get_user_service),
        jwt_service: JWTService = Depends(get_jwt_service),
) -> UserPublic:
    user_id = jwt_service.decode_to_user_id(JWT_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user