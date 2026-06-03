from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Product Image Backend"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    cors_origin_regex: str | None = r"https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+)(:\d+)?"

    database_url: str = "mysql+aiomysql://user:password@127.0.0.1:3306/product_ai"
    redis_url: str | None = None
    redis_host: str = "127.0.0.1"
    redis_port: int = Field(default=6379, ge=1)
    redis_db: int = Field(default=0, ge=0)
    redis_password: str | None = None

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_hours: int = Field(default=240, ge=1)
    token_idle_ttl_seconds: int = Field(default=7200, ge=60)

    openai_api_key: str | None = None
    openai_base_url: str | None = None
    gemini_api_key: str | None = None
    gemini_base_url: str | None = None
    jimeng_api_key: str | None = None
    jimeng_base_url: str | None = None
    alibaba_happyhouse_api_key: str | None = None
    alibaba_happyhouse_base_url: str | None = None
    provider_timeout_seconds: int = Field(default=600, ge=1)
    provider_max_retries: int = Field(default=2, ge=0)
    generated_image_storage_dir: str = "storage/gen_image"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def redis_dsn(self) -> str:
        if self.redis_url:
            return self.redis_url
        password = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{password}{self.redis_host}:{self.redis_port}/{self.redis_db}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
