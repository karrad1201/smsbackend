# conftest.py - ИСПРАВЛЕННАЯ версия
import asyncio
import pytest
import pytest_asyncio
import os
import sys
from unittest.mock import patch, AsyncMock, MagicMock
from decimal import Decimal
from datetime import datetime
import uuid

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


# УБИРАЕМ конфликтующую фикстуру event_loop
# @pytest.fixture(scope="session")
# def event_loop():
#     """Создаем event loop для тестов"""
#     try:
#         loop = asyncio.get_running_loop()
#     except RuntimeError:
#         loop = asyncio.new_event_loop()
#     yield loop
#     loop.close()


@pytest_asyncio.fixture(scope="session")
async def setup_db():
    """Создание и удаление таблиц перед всеми тестами"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def async_db_session():
    """Асинхронная сессия для интеграционных тестов"""
    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


# Переопределяем dependency приложения для использования тестовой сессии
async def override_get_db_session():
    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Применяем переопределение перед всеми тестами
@pytest_asyncio.fixture(scope="session", autouse=True)
async def override_dependencies():
    from src.infrastructure.database.connection import get_db_session
    app.dependency_overrides[get_db_session] = override_get_db_session

    # ДОБАВЛЯЕМ переопределение для аутентификации
    from src.core.di import get_current_user

    async def override_get_current_user():
        mock_user = AsyncMock()
        mock_user.id = 1
        mock_user.user_name = "test_user"
        mock_user.email = "test@test.com"
        mock_user.balance = 1000.0
        mock_user.api_key = "test_api_key_123"
        return mock_user

    app.dependency_overrides[get_current_user] = override_get_current_user

    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def async_client():
    """Асинхронный клиент для тестов"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def test_user_fixture():
    """Фикстура для создания тестового пользователя с уникальным ID"""
    from src.infrastructure.database.schemas import UserORM

    async with TestingSessionLocal() as session:
        # Генерируем уникальный ID для каждого теста
        unique_id = int(datetime.now().timestamp() * 1000) % 1000000
        test_user = UserORM(
            id=unique_id,
            user_name=f"test_user_{unique_id}",
            email=f"test_{unique_id}@test.com",
            balance=1000.0,
            api_key=f"test_api_key_{unique_id}",
            password_hash="test_password_hash",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        session.add(test_user)
        await session.commit()

        # Возвращаем данные пользователя для использования в тестах
        yield {
            "id": unique_id,
            "user_name": f"test_user_{unique_id}",
            "email": f"test_{unique_id}@test.com",
            "balance": 1000.0,
            "api_key": f"test_api_key_{unique_id}"
        }


@pytest_asyncio.fixture
async def authenticated_client():
    """Создает аутентифицированного асинхронного клиента"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Аутентификация уже настроена через dependency override
        yield client


@pytest.fixture
def mock_order_service(test_user_fixture):
    """Мок для OrderService"""
    mock_service = AsyncMock()

    # Настраиваем мок для создания заказа
    mock_order_dto = MagicMock()
    mock_order_dto.id = "test_order_123"
    mock_order_dto.service = "tg"
    mock_order_dto.service_name = "Telegram"
    mock_order_dto.country_code = "ru"
    mock_order_dto.country_name = "Russia"
    mock_order_dto.phone_number = "+79123456789"
    mock_order_dto.price = 10.0
    mock_order_dto.status = "PENDING_ORDER"
    mock_order_dto.created_at = datetime.now()
    mock_order_dto.activ_id = "ext_123"
    mock_order_dto.external_status = "ACCESS_NUMBER"
    mock_order_dto.user_id = test_user_fixture["id"]

    mock_service.create_order.return_value = mock_order_dto

    # Мок для опроса статуса
    mock_poll_response = MagicMock()
    mock_poll_response.status = "WAITING_CODE"
    mock_poll_response.code = None
    mock_poll_response.phone_number = "+79123456789"
    mock_poll_response.external_status = "STATUS_WAIT_CODE"
    mock_service.poll_order_status.return_value = mock_poll_response

    return mock_service


@pytest.fixture
def mock_user_service(test_user_fixture):
    """Мок для UserService"""
    mock_service = AsyncMock()

    mock_user = MagicMock()
    mock_user.id = test_user_fixture["id"]
    mock_user.user_name = test_user_fixture["user_name"]
    mock_user.email = test_user_fixture["email"]
    mock_user.balance = test_user_fixture["balance"]
    mock_user.api_key = test_user_fixture["api_key"]

    mock_service.get_by_id.return_value = mock_user
    return mock_service


def pytest_addoption(parser):
    """Добавляем флаг --real-api для запуска тестов с реальным API"""
    parser.addoption(
        "--real-api",
        action="store_true",
        default=False,
        help="Запускать тесты с реальными API вызовами"
    )


def pytest_configure(config):
    """Регистрируем маркер real_api"""
    config.addinivalue_line(
        "markers",
        "real_api: тесты с реальными API вызовами"
    )


@pytest.fixture(autouse=True)
def skip_real_api_tests(request):
    """Автоматически пропускает тесты с реальным API если не указан флаг --real-api"""
    if request.node.get_closest_marker('real_api'):
        if not request.config.getoption("--real-api"):
            pytest.skip("Нужно использовать флаг --real-api для запуска тестов с реальным API")