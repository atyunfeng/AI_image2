import pytest
from pydantic import ValidationError

from aiimage.config import Settings


def test_production_rejects_documented_local_secrets() -> None:
    with pytest.raises(ValidationError, match="must be changed in production"):
        Settings(
            env="production",
            database_url="postgresql+asyncpg://db/aiimage",
            redis_url="redis://redis/0",
            s3_endpoint="https://s3.example.com",
            s3_bucket="assets",
            s3_access_key="access",
            s3_secret_key="local-development-secret",
            secret_key_base64="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
            jwt_secret="local-development-jwt-secret-change-before-deploy",
            bootstrap_admin_email="admin@example.com",
            bootstrap_admin_password="LocalOnly-ChangeMe-2026",
        )
