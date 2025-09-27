# test_integeration_user_api.py
import pytest
from httpx import AsyncClient
from src.infrastructure.database.schemas import UserORM


class TestUserEndpoints:
    @pytest.mark.asyncio
    async def test_register_user_success(self, async_db_session, async_client: AsyncClient):
        user_data = {
            "user_name": "testuser",
            "password": "testpassword123",
            "email": "test@example.com"
        }

        response = await async_client.post("/user/register", json=user_data)
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user_name"] == "testuser"

        # Проверяем, что пользователь действительно создан в БД
        user = await async_db_session.get(UserORM, data["id"])
        assert user is not None
        assert user.user_name == "testuser"

    @pytest.mark.asyncio
    async def test_register_and_login_flow(self, async_db_session, async_client: AsyncClient):
        # Регистрация
        user_data = {
            "user_name": "loginuser",
            "password": "loginpassword123",
            "email": "login@example.com"
        }

        reg_response = await async_client.post("/user/register", json=user_data)
        assert reg_response.status_code == 200
        reg_data = reg_response.json()

        # Логин
        login_data = {
            "user_name": "loginuser",
            "password": "loginpassword123"
        }

        login_response = await async_client.post("/user/login", json=login_data)
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert "token" in login_data

    @pytest.mark.asyncio
    async def test_login_user_invalid_credentials(self, async_client: AsyncClient):
        login_data = {
            "user_name": "nonexistent",
            "password": "wrongpassword"
        }

        response = await async_client.post("/user/login", json=login_data)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_register_user_duplicate_username(self, async_client: AsyncClient):
        user_data = {
            "user_name": "duplicateuser",
            "password": "password123",
            "email": "dup1@example.com"
        }

        response1 = await async_client.post("/user/register", json=user_data)
        assert response1.status_code == 200

        # Пытаемся зарегистрировать с тем же username
        user_data["email"] = "dup2@example.com"
        response2 = await async_client.post("/user/register", json=user_data)
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_user_invalid_data(self, async_client: AsyncClient):
        # Нет пароля
        user_data_no_password = {"user_name": "nopassworduser"}
        response = await async_client.post("/user/register", json=user_data_no_password)
        assert response.status_code == 422

        # Нет username
        user_data_no_username = {"password": "password123"}
        response = await async_client.post("/user/register", json=user_data_no_username)
        assert response.status_code == 422

        # Пустой username
        user_data_empty_username = {
            "user_name": "",
            "password": "password123"
        }
        response = await async_client.post("/user/register", json=user_data_empty_username)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_current_user(self, authenticated_client: AsyncClient):
        response = await authenticated_client.get("/user/me")
        assert response.status_code == 200
        data = response.json()
        assert "user_name" in data
        assert "email" in data