from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    PROJECT_NAME: str = "Online Cinema"
    ENVIRONMENT: str
    DATABASE_POSTGRES_URL: str
    DATABASE_SQLITE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    @property
    def DATABASE_URL(self) -> str:
        if self.ENVIRONMENT == "local":
            return self.DATABASE_SQLITE_URL.replace("sqlite://", "sqlite+aiosqlite://")
        return self.DATABASE_POSTGRES_URL

    @property
    def DATABASE_URL_SYNC(self) -> str:
        """URL для Alembic (sync)"""
        if self.ENVIRONMENT == "local":
            return self.DATABASE_SQLITE_URL
        return self.DATABASE_POSTGRES_URL

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
