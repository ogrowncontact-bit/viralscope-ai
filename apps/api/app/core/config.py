from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuração central da aplicação, lida de variáveis de ambiente/.env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "local"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_cors_origins: str = "http://localhost:3000"

    database_url: str = "postgresql+asyncpg://viralscope:viralscope@localhost:5432/viralscope"
    redis_url: str = "redis://localhost:6379/0"

    clerk_jwks_url: str = ""
    clerk_issuer: str = ""
    clerk_webhook_secret: str = ""

    youtube_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.api_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
