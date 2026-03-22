from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Валидация и загрузка конфигурации приложения из переменных окружения (.env).
    """
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_DB: str
    POSTGRES_DB_PORT: int
    SECRET_KEY: str
    REDIS_PORT: int
    REDIS_DB: int
    ADMIN_EMAIL: str
    ADMIN_USERNAME: str
    SENTRY_DSN: str

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @property
    def database_url(self) -> str:
        """ Формирует DSN для ассинхронного подключения к PostgreSQL через asyncpg."""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_DB_PORT}/{self.POSTGRES_DB}"


settings = Settings()
