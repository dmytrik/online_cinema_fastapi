from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    PROJECT_NAME: str = "Online Cinema"
    ENVIRONMENT: str
    DATABASE_POSTGRES_URL: str
    DATABASE_SQLITE_URL: str
    SECRET_KEY_ACCESS: str
    SECRET_KEY_REFRESH: str
    JWT_SIGNING_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_DAYS: int = 5
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14

    @property
    def DATABASE_URL(self) -> str:
        if self.ENVIRONMENT == "local":
            return self.DATABASE_SQLITE_URL
        return self.DATABASE_POSTGRES_URL


    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
