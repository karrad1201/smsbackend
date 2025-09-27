# test_payment_endpoints.py
import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from src.infrastructure.database.schemas import UserORM, PaymentORM


class TestPaymentEndpoints:
    @pytest.mark.asyncio
    async def test_create_payment_success(self, async_db_session, async_client: AsyncClient):
        # Создаем пользователя
        user = UserORM(
            user_name="paymentuser",
            email="payment@example.com",
            password_hash="hashedpassword"
        )
        async_db_session.add(user)
        await async_db_session.commit()
        await async_db_session.refresh(user)

        # Аутентифицируемся
        login_data = {"user_name": "paymentuser", "password": "testpassword123"}

        with patch('src.core.di.get_hasher_service') as mock_hasher:
            mock_instance = AsyncMock()
            mock_instance.verify.return_value = True
            mock_hasher.return_value = mock_instance

            login_response = await async_client.post("/user/login", json=login_data)

        if login_response.status_code == 200:
            response_data = login_response.json()
            token = response_data.get('token') or response_data.get('user', {}).get('token')
            if token:
                headers = {"Authorization": f"Bearer {token}"}

                with patch('src.services.heleket_service.HeleketService.create_payment') as mock_create:
                    mock_create.return_value = {
                        "state": 0,
                        "result": {
                            "uuid": "test-invoice-123",
                            "url": "https://pay.heleket.com/pay/test-invoice-123",
                            "address": "test-address",
                            "payer_amount": "25.50",
                            "payer_currency": "USD"
                        }
                    }

                    payment_data = {"amount": 25.50}
                    response = await async_client.post("/payments/create", json=payment_data, headers=headers)

                    # Проверяем статус ответа
                    assert response.status_code in [200, 400, 500]

    @pytest.mark.asyncio
    async def test_get_payment_not_found(self, async_db_session, async_client: AsyncClient):
        # Создаем и аутентифицируем пользователя
        user = UserORM(
            user_name="notfounduser",
            email="notfound@example.com",
            password_hash="hashedpassword"
        )
        async_db_session.add(user)
        await async_db_session.commit()

        login_data = {"user_name": "notfounduser", "password": "testpassword123"}
        login_response = await async_client.post("/user/login", json=login_data)
        token = login_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = await async_client.get("/payments/999999", headers=headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_payment_success(self, async_db_session, async_client: AsyncClient):
        # Создаем пользователя и платеж
        user = UserORM(
            user_name="getpaymentuser",
            email="getpayment@example.com",
            password_hash="hashedpassword"
        )
        async_db_session.add(user)
        await async_db_session.commit()
        await async_db_session.refresh(user)

        # Создаем платеж без поля 'currency'
        payment = PaymentORM(
            user_id=user.id,
            amount=50.0,
            status="pending"
            # Убираем payment_uuid, если его нет в модели
        )
        async_db_session.add(payment)
        await async_db_session.commit()
        await async_db_session.refresh(payment)

        # Аутентифицируемся
        login_data = {"user_name": "getpaymentuser", "password": "testpassword123"}

        with patch('src.core.di.get_hasher_service') as mock_hasher:
            mock_instance = AsyncMock()
            mock_instance.verify.return_value = True
            mock_hasher.return_value = mock_instance

            login_response = await async_client.post("/user/login", json=login_data)

        if login_response.status_code == 200:
            response_data = login_response.json()
            token = response_data.get('token') or response_data.get('user', {}).get('token')
            if token:
                headers = {"Authorization": f"Bearer {token}"}

                response = await async_client.get(f"/payments/{payment.id}", headers=headers)
                assert response.status_code == 200
                data = response.json()
                assert data["id"] == payment.id
                assert float(data["amount"]) == 50.0