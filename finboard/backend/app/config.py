from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "FinBoard"
    debug: bool = True

    # Database — SQLite (zero dependency, local file)
    database_url: str = "sqlite+aiosqlite:///finboard.db"

    # DeepSeek
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"

    # Proxy
    http_proxy: str | None = None
    https_proxy: str | None = None

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
