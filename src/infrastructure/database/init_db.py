from src.infrastructure.database.base import Base
from src.infrastructure.database.connection import engine

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
