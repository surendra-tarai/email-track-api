from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    mongodb_url: str
    mongodb_db: str = "email_tracker"
    redis_url: str
    base_url: str = "http://localhost:8000"
    short_code_length: int = 8


settings = Settings()
