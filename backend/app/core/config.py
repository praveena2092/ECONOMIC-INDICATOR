"""Typed, validated application settings loaded from environment / .env."""
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"
    enable_api_docs: bool = True

    database_url: str = Field(..., min_length=10)
    db_pool_min: int = 1
    db_pool_max: int = 5

    jwt_secret: str = Field(..., min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = Field(60, ge=1, le=1440)

    cors_origins: str = "http://localhost:5173"

    collectors_enabled: bool = True
    nse_refresh_seconds: int = Field(60, ge=15)
    nse_off_hours_refresh_seconds: int = Field(900, ge=60)
    macro_refresh_hours: int = Field(6, ge=1)
    http_timeout_seconds: float = Field(10, gt=0)
    http_max_retries: int = Field(2, ge=0, le=5)
    rbi_inflation_target: float = 4.0

    nse_base_url: str = "https://www.nseindia.com"
    worldbank_base_url: str = "https://api.worldbank.org/v2"
    imf_base_url: str = "https://www.imf.org/external/datamapper/api/v1"
    yahoo_chart_url: str = "https://query1.finance.yahoo.com/v8/finance/chart"

    @field_validator("cors_origins")
    @classmethod
    def _no_wildcard(cls, v: str) -> str:
        if "*" in v:
            raise ValueError("CORS_ORIGINS must list explicit origins; '*' is not allowed")
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip().rstrip("/") for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
