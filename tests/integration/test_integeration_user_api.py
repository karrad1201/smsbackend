# test_integration_user_api.py
import pytest
from fastapi.testclient import TestClient
from src.core.domain.entity.user import UserCreate


@pytest.mark.integration
class TestUserIntegration:
    def test_get_users_integration(self, client: TestClient):
        user_data = {
            "name": "newuser",
            "password": "newpassword123"
        }

        response = client.post("/user/register", json=user_data)

        assert response.status_code == 200
        assert "token" in response.json()

        users_response = client.get("/user/users")
        users = users_response.json()
        assert len(users) == 1

        new_user = next((u for u in users if u["name"] == "newuser"), None)
        print(new_user)
        assert new_user is not None


        response = client.get("/user/users")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["name"] == "newuser"

    def test_register_user_integration(self, client: TestClient):
        user_data = {
            "name": "newuser1",
            "password": "newpassword123"
        }

        response = client.post("/user/register", json=user_data)

        assert response.status_code == 200
        assert "token" in response.json()

        users_response = client.get("/user/users")
        users = users_response.json()
        assert len(users) == 2

        new_user = next((u for u in users if u["name"] == "newuser"), None)
        print(new_user)
        assert new_user is not None

    def test_register_user_duplicate_integration(self, client: TestClient):
        user_data = {
            "name": "user1",
            "password": "password123"
        }

        client.post("/user/register", json=user_data)

        user_data = {
            "name": "user1",
            "password": "password123"
        }

        response = client.post("/user/register", json=user_data)

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()
