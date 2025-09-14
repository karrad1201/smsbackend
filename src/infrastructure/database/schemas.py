from sqlalchemy import Column, Integer, String
from src.infrastructure.database.base import Base

class UserORM(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)


__all__ = ["UserORM"]