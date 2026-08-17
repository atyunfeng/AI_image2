from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AIIMAGE_",
        env_file=".env",
        extra="ignore",
    )

    env: str = "development"
    database_url: str
    redis_url: str
    s3_endpoint: str
    s3_bucket: str
    s3_access_key: str
    s3_secret_key: str
    secret_key_base64: str
    jwt_secret: str
    bootstrap_admin_email: str
    bootstrap_admin_password: str


@lru_cache
def get_settings() -> Settings:
    return Settings()

