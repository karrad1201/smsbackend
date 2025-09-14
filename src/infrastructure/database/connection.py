import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

TESTING = os.getenv("TESTING", "0") == "1"

if TESTING:
    from src.core.config import TEST_DATABASE_URL
    DATABASE_URL = TEST_DATABASE_URL
    engine = create_async_engine(DATABASE_URL, echo=True)
else:
    from src.core.config import DATABASE_URL
    engine = create_async_engine(DATABASE_URL, echo=True, pool_size=10, max_overflow=20, pool_timeout=30)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
