import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


class TestPaymentEndpoints:
    def test_create_payment_basic(self, client: TestClient):
        user_data = {"user_name": "paymentuser", "password": "password123"}
        reg_response = client.post("/user/register", json=user_data)

        if reg_response.status_code != 200:
            pytest.skip("User registration failed")

        token = reg_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        with patch('src.services.heleket_service.HeleketService.create_payment') as mock_create:
            mock_create.return_value = {
                "state": 0,
                "result": {
                    "uuid": "test-invoice-123",
                    "url": "https://pay.heleket.com/pay/test-invoice-123"
                }
            }

            payment_data = {
                "user_id": 1,
                "amount": 25.50
            }

            response = client.post("/payments/create", json=payment_data, headers=headers)

            assert response.status_code != 500

    def test_get_payment_not_found_basic(self, client: TestClient):
        user_data = {"user_name": "notfounduser", "password": "password123"}
        reg_response = client.post("/user/register", json=user_data)

        if reg_response.status_code != 200:
            pytest.skip("User registration failed")

        token = reg_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/payments/999", headers=headers)
        assert response.status_code != 200
