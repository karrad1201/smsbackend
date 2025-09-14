from sqlalchemy.orm import declarative_base
from src.infrastructure.database.schemas import *   # В __all__ определены все модели

Base = declarative_base()