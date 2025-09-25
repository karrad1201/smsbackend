from fastapi import APIRouter, Depends, status, Form
from fastapi.exceptions import HTTPException
from src.core.di import get_user_service, get_jwt_service, get_current_user, get_hasher_service
from src.core.logging_config import get_logger
from src.core.exceptions.exceptions import AlreadyExistsException
from src.core.domain.dto.user_dto import (
    UserProfileDTO,
    UserCreateDTO,
    UserUpdateDTO,
    UserBalanceDTO,
    UserLoginDTO
)
from src.core.domain.dto.response_dto import StandardResponse
from src.core.domain.entity.user import User

user_router = APIRouter(prefix="/user")
logger = get_logger(__name__)


@user_router.get("/users", response_model=list[UserProfileDTO])
async def get_users(user_service=Depends(get_user_service)) -> list[UserProfileDTO]:
    try:
        return await user_service.get_all_users()
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@user_router.post("/register")
async def register_user(
        user_dto: UserCreateDTO,
        user_service=Depends(get_user_service),
        jwt_service=Depends(get_jwt_service)
):
    try:
        user = await user_service.register_user(user_dto)
        user_id = user.id
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user"
            )

        token = jwt_service.create_access_token(user_id)
        logger.info(f"User {user_dto.user_name} registered with id {user_id}, token generated")
        return {"token": token, "user_id": user_id}

    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except AlreadyExistsException as e:
        logger.warning(f"User {user_dto.user_name} already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error registering user {user_dto.user_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@user_router.post("/login")
async def login_user(
        login_dto: UserLoginDTO,
        user_service=Depends(get_user_service),
        jwt_service=Depends(get_jwt_service),
        hasher_service=Depends(get_hasher_service)
):
    try:
        user = await user_service.get_by_username(login_dto.user_name)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        password_hash = await user_service.get_password_hash(user.id)
        if not hasher_service.verify(login_dto.password, password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        token = jwt_service.create_access_token(user.id)
        logger.info(f"User {login_dto.user_name} logged in, token generated for user_id: {user.id}")
        return {'user': user, 'token': token}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error logging in user {login_dto.user_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@user_router.get("/me", response_model=UserProfileDTO)
async def get_current_user_profile(
        current_user: User = Depends(get_current_user),
        user_service=Depends(get_user_service)
):
    try:
        return user_service.user_mapper.entity_to_profile_dto(current_user)
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@user_router.put("/me", response_model=UserProfileDTO)
async def update_user_profile(
        update_dto: UserUpdateDTO,
        current_user: User = Depends(get_current_user),
        user_service=Depends(get_user_service)
):
    try:
        if update_dto.first_name is not None:
            current_user.first_name = update_dto.first_name
        if update_dto.last_name is not None:
            current_user.last_name = update_dto.last_name
        if update_dto.email is not None:
            current_user.email = update_dto.email
        if update_dto.language is not None:
            current_user.language = update_dto.language

        updated_user = await user_service.update_user(current_user)
        return user_service.user_mapper.entity_to_profile_dto(updated_user)

    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@user_router.post("/change-password")
async def change_password(
        current_password: str = Form(...),
        new_password: str = Form(...),
        current_user: User = Depends(get_current_user),
        user_service=Depends(get_user_service),
        hasher_service=Depends(get_hasher_service)
):
    try:
        current_password_hash = await user_service.get_password_hash(current_user.id)

        if not hasher_service.verify(current_password, current_password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )

        await user_service.update_password(current_user.id, new_password)

        logger.info(f"User {current_user.user_name} changed password")
        return StandardResponse(
            success=True,
            message="Password changed successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@user_router.get("/balance", response_model=UserBalanceDTO)
async def get_user_balance(
        current_user: User = Depends(get_current_user)
):
    try:
        return UserBalanceDTO(balance=current_user.balance)
    except Exception as e:
        logger.error(f"Error getting user balance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@user_router.post("/generate-api-key")
async def generate_api_key(
        current_user: User = Depends(get_current_user),
        user_service=Depends(get_user_service)
):
    try:
        import secrets
        api_key = secrets.token_urlsafe(32)

        await user_service.update_api_key(current_user.id, api_key)

        logger.info(f"User {current_user.user_name} generated new API key")
        return StandardResponse(
            success=True,
            message="API key generated successfully",
            data={"api_key": api_key}
        )

    except Exception as e:
        logger.error(f"Error generating API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@user_router.delete("/account")
async def delete_user_account(
        current_user: User = Depends(get_current_user),
        user_service=Depends(get_user_service)
):
    try:
        await user_service.delete_user(current_user.id)

        logger.info(f"User {current_user.user_name} deleted account")
        return StandardResponse(
            success=True,
            message="Account deleted successfully"
        )

    except Exception as e:
        logger.error(f"Error deleting user account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

