import pytest
from unittest.mock import AsyncMock, patch
from src.services.user_service import UserService
from src.core.domain.entity.user import User
from src.core.domain.dto.user_dto import UserCreateDTO
from src.core.exceptions.exceptions import AlreadyExistsException
from datetime import datetime


class TestUserService:
    @pytest.fixture
    def mock_repo(self):
        return AsyncMock()

    @pytest.fixture
    def user_service(self, mock_repo):
        return UserService(mock_repo)

    @pytest.mark.asyncio
    async def test_register_user_success(self, user_service, mock_repo):
        user_data = UserCreateDTO(
            user_name="testuser",
            password="password123",
            email="test@example.com"
        )

        mock_user = User(
            id=1,
            user_name="testuser",
            email="test@example.com",
            balance=0.0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        mock_repo.get_by_username.return_value = None
        mock_repo.create.return_value = mock_user

        with patch.object(user_service, 'hasher_service') as mock_hasher:
            mock_hasher.hash.return_value = "hashed_password"

            result = await user_service.register_user(user_data)

        assert result.id == 1
        assert result.user_name == "testuser"
        mock_repo.get_by_username.assert_called_once_with("testuser")
        mock_hasher.hash.assert_called_once_with("password123")

    @pytest.mark.asyncio
    async def test_register_user_already_exists(self, user_service, mock_repo):
        user_data = UserCreateDTO(
            user_name="existinguser",
            password="password123",
            email="existing@example.com"
        )

        existing_user = User(
            id=1,
            user_name="existinguser",
            email="existing@example.com",
            balance=0.0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        mock_repo.get_by_username.return_value = existing_user

        with pytest.raises(AlreadyExistsException):
            await user_service.register_user(user_data)
