import asyncio
import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.core.config import Settings

os.environ["TESTING"] = "1"

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import event
from sqlalchemy.engine import Engine

from src.infrastructure.database.schemas import Base, UserORM, PaymentORM
from src.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if engine.dialect.name == "sqlite":
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


@pytest.fixture(scope="session")
def test_settings():
    return Settings(
        HELEKET_MERCHANT_ID="test_merchant",
        HELEKET_API_KEY="test_api_key",
        HELEKET_SECRET_KEY="test_secret_key",
        BASE_URL="http://localhost:8000",
        FRONTEND_URL="http://localhost:3000",
    )


@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session():
    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def override_settings(test_settings):
    import src.core.config as config
    original_settings = getattr(config, 'settings', None)
    config.settings = test_settings
    yield
    if original_settings:
        config.settings = original_settings


@pytest.fixture
async def test_users(db_session):
    await db_session.execute(PaymentORM.__table__.delete())
    await db_session.execute(UserORM.__table__.delete())

    test_users = [
        UserORM(
            user_name="testuser1",
            password_hash="hash1",
            email="user1@test.com",
            balance=100.0,
            is_admin=False
        ),
        UserORM(
            user_name="testuser2",
            password_hash="hash2",
            email="user2@test.com",
            balance=50.0,
            is_admin=False
        )
    ]

    db_session.add_all(test_users)
    await db_session.commit()
    return test_users


@pytest.fixture
def mock_heleket_service():
    from unittest.mock import AsyncMock
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


@pytest.fixture
async def authenticated_client(client, db_session):
    from src.infrastructure.database.schemas import UserORM
    from src.services.haser_service import HasherService

    hasher = HasherService()
    test_user = UserORM(
        user_name="test_auth_user",
        password_hash=hasher.hash("testpassword123"),
        email="auth@test.com",
        balance=100.0
    )

    db_session.add(test_user)
    await db_session.commit()
    await db_session.refresh(test_user)

    login_data = {
        "user_name": "test_auth_user",
        "password": "testpassword123"
    }

    login_response = client.post("/user/login", json=login_data)
    if login_response.status_code == 200:
        token = login_response.json()["token"]
        client.headers.update({"Authorization": f"Bearer {token}"})

    yield client

    client.headers.pop("Authorization", None)


@pytest.fixture
async def admin_client(client, db_session):
    from src.infrastructure.database.schemas import UserORM
    from src.services.haser_service import HasherService

    hasher = HasherService()
    admin_user = UserORM(
        user_name="test_admin",
        password_hash=hasher.hash("adminpassword123"),
        email="admin@test.com",
        balance=0.0,
        is_admin=True
    )

    db_session.add(admin_user)
    await db_session.commit()
    await db_session.refresh(admin_user)

    login_data = {
        "user_name": "test_admin",
        "password": "adminpassword123"
    }

    login_response = client.post("/user/login", json=login_data)
    if login_response.status_code == 200:
        token = login_response.json()["token"]
        client.headers.update({"Authorization": f"Bearer {token}"})

    yield client

    client.headers.pop("Authorization", None)
