import pytest
from fastapi.testclient import TestClient

def test_get_users(client: TestClient):
    response = client.get("/user/users")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
