# conftest.py
import asyncio
import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

os.environ["TESTING"] = "1"

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.infrastructure.database.schemas import Base, UserORM
from src.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# Фикстура для тестовой сессии
@pytest.fixture
async def db_session():
    async with TestingSessionLocal() as session:
        yield session


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    await create_tables()
    yield
    await drop_tables()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


# Фикстура для тестовых данных
@pytest.fixture(autouse=True)
async def create_test_data(db_session):
    """Создаем тестовых пользователей перед каждым тестом"""
    try:
        # Очищаем таблицу
        await db_session.execute(UserORM.__table__.delete())

        # Создаем тестовых пользователей
        test_users = [
            UserORM(name="user1", password_hash="hash1"),
            UserORM(name="user2", password_hash="hash2")
        ]

        db_session.add_all(test_users)
        await db_session.commit()
        yield

    finally:
        # Всегда очищаем после теста
        await db_session.execute(UserORM.__table__.delete())
        await db_session.commit()