import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

TESTING = os.getenv("TESTING", "0") == "1"

if TESTING:
    from src.core.config import TEST_DATABASE_URL
    DATABASE_URL = TEST_DATABASE_URL
    engine = create_async_engine(DATABASE_URL, echo=True)
else:
    from src.core.config import DATABASE_URL

    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_size=25,
        max_overflow=50,
        pool_timeout=60,
        pool_recycle=1800,
        pool_pre_ping=True
    )

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db_session() -> AsyncSession:
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()