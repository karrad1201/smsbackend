# conftest.py (исправленные фикстуры)
import asyncio
import pytest
import pytest_asyncio
import os
import sys
from unittest.mock import patch, AsyncMock
from decimal import Decimal

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

os.environ["TESTING"] = "1"

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import event
from sqlalchemy.engine import Engine
from httpx import AsyncClient

from src.infrastructure.database.schemas import Base, UserORM, PaymentORM
from src.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(TEST_DATABASE_URL, echo=True)
TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if engine.dialect.name == "sqlite":
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

@pytest.fixture(scope="session")
def test_settings():
    return {
        "HELEKET_MERCHANT_ID": "test_merchant",
        "HELEKET_API_KEY": "test_api_key",
        "HELEKET_SECRET_KEY": "test_secret_key",
        "BASE_URL": "http://localhost:8000",
        "FRONTEND_URL": "http://localhost:3000",
    }

@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def async_db_session():
    """Асинхронная сессия для async тестов"""
    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()

@pytest_asyncio.fixture
async def async_client():
    """Асинхронный клиент для тестов"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def authenticated_client(async_db_session):
    """Создает аутентифицированного асинхронного клиента"""
    # Сначала загружаем тестовые данные
    await load_test_data(async_db_session)

    # Создаем тестового пользователя
    user = UserORM(
        user_name="test_auth_user",
        email="auth@test.com",
        password_hash="hashed_test_password",
        balance=1000.0
    )
    async_db_session.add(user)
    await async_db_session.commit()
    await async_db_session.refresh(user)

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Логинимся с моком
        login_data = {
            "user_name": "test_auth_user",
            "password": "testpassword123"
        }

        # Правильный путь для мока HasherService
        with patch('src.core.di.get_hasher_service') as mock_hasher:
            mock_instance = AsyncMock()
            mock_instance.verify.return_value = True
            mock_hasher.return_value = mock_instance

            response = await client.post("/user/login", json=login_data)

        if response.status_code == 200:
            response_data = response.json()
            # Исправляем получение токена (структура ответа)
            if 'token' in response_data:
                token = response_data['token']
                client.headers.update({"Authorization": f"Bearer {token}"})
            elif 'user' in response_data and 'token' in response_data['user']:
                token = response_data['user']['token']
                client.headers.update({"Authorization": f"Bearer {token}"})
            else:
                print("Warning: Token not found in login response")

        yield client

async def load_test_data(async_db_session):
    """Функция для загрузки тестовых данных"""
    from src.infrastructure.database.schemas import (
        ProviderRoutesORM, ProviderORM, ServiceReferenceORM,
        CountryReferenceORM, OrderORM, StatusTypeORM
    )

    try:
        # Очищаем таблицы в правильном порядке (с учетом foreign keys)
        tables_to_clear = [OrderORM, PaymentORM, ProviderRoutesORM, ProviderORM,
                           ServiceReferenceORM, CountryReferenceORM, StatusTypeORM, UserORM]

        for table in tables_to_clear:
            await async_db_session.execute(table.__table__.delete())

        # Создаем статусы заказов
        status_types = [
            StatusTypeORM(id=1, code="PENDING", name_en="Pending", name_ru="В ожидании"),
            StatusTypeORM(id=2, code="COMPLETED", name_en="Completed", name_ru="Завершен"),
            StatusTypeORM(id=3, code="CANCELLED", name_en="Cancelled", name_ru="Отменен"),
        ]

        # Создаем тестовые сервисы
        services = [
            ServiceReferenceORM(code="telegram", name="Telegram", category="social",
                                is_popular=True, is_active=True),
            ServiceReferenceORM(code="whatsapp", name="WhatsApp", category="social",
                                is_popular=True, is_active=True),
        ]

        # Создаем тестовые страны
        countries = [
            CountryReferenceORM(code="US", name_ru="США", name_en="USA",
                                is_active=True, is_popular=True),
            CountryReferenceORM(code="RU", name_ru="Россия", name_en="Russia",
                                is_active=True, is_popular=True),
        ]

        # Создаем провайдера
        provider = ProviderORM(
            name="test_provider",
            adapter_class="TestAdapter",
            config={},
            is_active=True,
            display_name="Test Provider"
        )

        # Создаем маршруты
        provider_routes = [
            ProviderRoutesORM(
                provider=provider,
                country_code="US",
                service_code="telegram",
                provider_country_code="US",
                provider_service_code="tg",
                cost_price=Decimal('5.0'),
                client_price=Decimal('10.0'),
                vip_client_price=Decimal('9.0'),
                available_count=100,
                is_active=True,
                id=1
            ),
            ProviderRoutesORM(
                provider=provider,
                country_code="RU",
                service_code="telegram",
                provider_country_code="RU",
                provider_service_code="tg",
                cost_price=Decimal('4.0'),
                client_price=Decimal('8.0'),
                vip_client_price=Decimal('7.0'),
                available_count=50,
                is_active=True,
                id=2
            ),
        ]

        # Добавляем все в сессию
        async_db_session.add_all(status_types + services + countries + [provider] + provider_routes)
        await async_db_session.commit()

        print("✅ Тестовые данные загружены")

    except Exception as e:
        print(f"❌ Ошибка загрузки тестовых данных: {e}")
        await async_db_session.rollback()
        raise

@pytest_asyncio.fixture(autouse=True)
async def auto_load_test_data(async_db_session):
    """Автоматическая загрузка тестовых данных перед каждым тестом"""
    await load_test_data(async_db_session)

# Мок для платежной системы (синхронный, поэтому оставляем pytest.fixture)
@pytest.fixture
def mock_heleket_service():
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
    mock_service.check_payment_status.return_value = {"status": "paid"}
    return mock_service