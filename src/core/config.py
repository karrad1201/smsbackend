import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION = os.getenv("JWT_EXPIRATION", "4000")

from dataclasses import dataclass

@dataclass
class Settings():
    HELEKET_MERCHANT_ID: str
    HELEKET_API_KEY: str
    HELEKET_SECRET_KEY: str

    BASE_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:3000"

    class Config:
        env_file = ".env"


settings = Settings(
    HELEKET_MERCHANT_ID=os.getenv("HELEKET_MERCHANT_ID"),
    HELEKET_API_KEY=os.getenv("HELEKET_API_KEY"),
    HELEKET_SECRET_KEY=os.getenv("HELEKET_SECRET_KEY")
)