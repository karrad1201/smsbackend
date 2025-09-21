from src.infrastructure.database.base import Base
from src.infrastructure.database.connection import engine
from src.core.logging_config import get_logger
import asyncio
from sqlalchemy.exc import OperationalError
from sqlalchemy import text

logger = get_logger(__name__)


async def wait_for_db(max_retries: int = 10, delay: float = 2.0):
    for attempt in range(max_retries):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("✅ Database connection established")
            return True
        except OperationalError as e:
            logger.warning(f"⏳ Database not ready (attempt {attempt + 1}/{max_retries}): {e}")
            await asyncio.sleep(delay)
    logger.error("❌ Database connection failed after multiple attempts")
    return False


async def create_tables():
    logger.info("🔄 Auto-creating/updating database tables...")

    if not await wait_for_db():
        raise OperationalError("Cannot connect to database")

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ Database tables created/updated successfully")

    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        raise


async def sync_database():
    logger.info("🔄 Synchronizing database structure with ORM...")

    if not await wait_for_db():
        raise OperationalError("Cannot connect to database")

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database structure synchronized successfully!")
        return True
    except Exception as e:
        logger.error(f"❌ Error synchronizing database: {e}")
        raise