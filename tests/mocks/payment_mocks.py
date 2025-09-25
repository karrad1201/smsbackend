from unittest.mock import AsyncMock


def create_mock_heleket_service():
    mock_service = AsyncMock()

    mock_service.create_payment.return_value = {
        "state": 0,
        "result": {
            "uuid": "test-uuid-123",
            "url": "https://pay.heleket.com/pay/test-uuid-123",
            "address": "0x1234567890",
            "payer_amount": "100.0",
            "payer_currency": "USDT"
        }
    }

    return mock_service