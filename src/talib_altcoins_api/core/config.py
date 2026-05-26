from __future__ import annotations

from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

Environment = Literal["development", "production"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        extra="ignore",
    )

    environment: Environment = "production"
    host: str = "0.0.0.0"  # noqa: S104
    port: int = Field(default=5001, ge=1, le=65535)
    workers: int = Field(default=2, ge=1, le=64)
    reload: bool = False

    log_level: str = "INFO"
    log_json: bool = True

    cors_allow_origins: Annotated[list[str], NoDecode] = Field(default_factory=list)

    sentry_dsn: str | None = None

    rate_limit: str = "60/minute"

    cache_ttl_seconds: int = Field(default=30, ge=0, le=3600)

    ccxt_timeout_ms: int = Field(default=10_000, ge=1_000, le=60_000)
    ccxt_max_retries: int = Field(default=3, ge=0, le=10)

    adx_period: int = Field(default=14, ge=2, le=500)
    rsi_period: int = Field(default=14, ge=2, le=500)
    sma_short_period: int = Field(default=5, ge=2, le=500)
    sma_mid_period: int = Field(default=10, ge=2, le=500)
    sma_long_period: int = Field(default=30, ge=2, le=500)
    ma_50_period: int = Field(default=50, ge=2, le=500)
    ma_100_period: int = Field(default=100, ge=2, le=500)
    macd_fast: int = Field(default=12, ge=2, le=500)
    macd_slow: int = Field(default=26, ge=2, le=500)
    macd_signal: int = Field(default=9, ge=2, le=500)
    linear_reg_period: int = Field(default=14, ge=2, le=500)

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def _split_csv(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    get_settings.cache_clear()
