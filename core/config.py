import os

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class BaseAppSettings(BaseSettings):
    PROJECT_NAME: str = "Online Cinema"
    ENVIRONMENT: str
    DATABASE_SQLITE_URL: str
    STRIPE_SECRET_KEY: str
    SECRET_KEY_ACCESS: str
    SECRET_KEY_REFRESH: str
    JWT_SIGNING_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_DAYS: int = 5
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14

    class Config:
        env_file = ".env"
        extra = "allow"


class Settings(BaseAppSettings):
    # Celery settings
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    CELERY_TIMEZONE: str = "UTC"
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_TIME_LIMIT: int = 60
    CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP: bool = True

    # Postgres settings
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "test_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "test_password")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "test_host")
    POSTGRES_DB_PORT: int = int(os.getenv("POSTGRES_DB_PORT", 5432))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "test_db")

    @property
    def DATABASE_URL(self) -> str:
        if self.ENVIRONMENT == "local":
            return self.DATABASE_SQLITE_URL
        return (f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
                f"{self.POSTGRES_HOST}:{self.POSTGRES_DB_PORT}/{self.POSTGRES_DB}")


settings = Settings()
