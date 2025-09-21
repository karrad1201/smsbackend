import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from src.core.domain.entity.user import UserPublic


def test_get_users(client: TestClient):
    mock_user_service = AsyncMock()
    mock_users = [
        UserPublic(id=1, name="user1"),
        UserPublic(id=2, name="user2")
    ]
    mock_user_service.get_users.return_value = mock_users
    from src.main import app
    from src.core.di.service import get_user_service

    app.dependency_overrides[get_user_service] = lambda: mock_user_service
    response = client.get("/user/users")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["name"] == "user1"
    assert data[1]["name"] == "user2"

    mock_user_service.get_users.assert_called_once()

    app.dependency_overrides.clear()


def test_register_user_success(client: TestClient):
    mock_user_service = AsyncMock()
    mock_user_service.register_user.return_value = 1

    mock_jwt_service = MagicMock()
    mock_jwt_service.encode.return_value = "mock_jwt_token"


    from src.main import app
    from src.core.di.service import get_user_service, get_jwt_service

    app.dependency_overrides[get_user_service] = lambda: mock_user_service
    app.dependency_overrides[get_jwt_service] = lambda: mock_jwt_service

    user_data = {
        "name": "testuser",
        "password": "testpassword123"
    }

    response = client.post("/user/register", json=user_data)

    assert response.status_code == 200
    assert response.json() == {"token": "mock_jwt_token"}

    mock_user_service.register_user.assert_called_once()
    mock_jwt_service.encode.assert_called_once_with({'user_id': 1})


def test_register_user_failure(client: TestClient):
    mock_user_service = AsyncMock()
    mock_user_service.register_user.side_effect = Exception("Database error")

    from src.main import app
    from src.core.di.service import get_user_service

    app.dependency_overrides[get_user_service] = lambda: mock_user_service

    user_data = {
        "id": 1,
        "name": "testuser",
        "password": "testpassword123"
    }

    response = client.post("/user/register", json=user_data)

    assert response.status_code == 500