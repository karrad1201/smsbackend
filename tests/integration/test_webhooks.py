import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock


class TestWebhooks:
    def test_heleket_webhook_basic(self, client: TestClient):
        user_data = {"user_name": "webhookuser", "password": "password123"}
        reg_response = client.post("/user/register", json=user_data)

        if reg_response.status_code != 200:
            pytest.skip("User registration failed")

        with patch('src.services.heleket_service.HeleketService') as MockHeleket:
            mock_heleket = AsyncMock()
            MockHeleket.return_value = mock_heleket

            mock_heleket.create_payment.return_value = {
                "state": 0,
                "result": {"uuid": "webhook-test-123", "url": "https://test.com"}
            }

            token = reg_response.json()["token"]
            headers = {"Authorization": f"Bearer {token}"}
            payment_data = {"user_id": 1, "amount": 15.0}

            with patch('src.presentation.api.payments.payment_router.get_heleket_service'):
                client.post("/payments/create", json=payment_data, headers=headers)

        webhook_data = {
            "uuid": "webhook-test-123",
            "payment_status": "paid",
            "txid": "0xabc123456789"
        }

        response = client.post("/webhooks/heleket", json=webhook_data)

        assert response.status_code == 200
        assert "status" in response.json()

    def test_heleket_webhook_invalid_invoice(self, client: TestClient):
        webhook_data = {
            "uuid": "nonexistent-invoice",
            "payment_status": "paid"
        }

        response = client.post("/webhooks/heleket", json=webhook_data)
        assert response.status_code == 200
        result = response.json()
        assert "status" in result
