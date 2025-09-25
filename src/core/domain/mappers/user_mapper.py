from src.core.domain.entity.user import User, UserCreate
from src.core.domain.dto.user_dto import UserProfileDTO, UserCreateDTO


class UserMapper:
    @staticmethod
    def entity_to_profile_dto(user: User) -> UserProfileDTO:
        return UserProfileDTO(
            id=user.id,
            user_name=user.user_name,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            balance=user.balance,
            discount_rate=user.discount_rate,
            language=user.language,
            created_at=user.created_at
        )

    @staticmethod
    def create_dto_to_entity(user_dto: UserCreateDTO) -> UserCreate:
        return UserCreate(
            user_name=user_dto.user_name,
            password=user_dto.password,
            email=user_dto.email,
            first_name=user_dto.first_name,
            last_name=user_dto.last_name
        )

    @staticmethod
    def entity_to_balance_dto(user: User) -> dict:
        return {"balance": user.balance}