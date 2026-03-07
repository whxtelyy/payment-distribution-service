from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_DB_PORT: int
    SECRET_KEY: str
    
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
