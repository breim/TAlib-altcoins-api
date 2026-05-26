from __future__ import annotations

from functools import lru_cache
from typing import Any, Protocol

import ccxt
import structlog
from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from talib_altcoins_api.core.config import get_settings

logger = structlog.get_logger(__name__)


class UnknownExchangeError(Exception):
    pass


class UpstreamFetchError(Exception):
    pass


class ExchangeClient(Protocol):
    def fetch_ohlcv(
        self, symbol: str, timeframe: str, since: int | None = None, limit: int | None = None
    ) -> list[list[float]]: ...


@lru_cache(maxsize=32)
def get_exchange_client(name: str) -> ExchangeClient:
    settings = get_settings()
    try:
        cls: Any = getattr(ccxt, name)
    except AttributeError as exc:
        raise UnknownExchangeError(name) from exc
    client = cls({"enableRateLimit": True, "timeout": settings.ccxt_timeout_ms})
    return client  # type: ignore[no-any-return]


def fetch_ohlcv(exchange: str, symbol: str, interval: str, limit: int) -> list[list[float]]:
    settings = get_settings()
    client = get_exchange_client(exchange)

    @retry(
        reraise=True,
        stop=stop_after_attempt(settings.ccxt_max_retries + 1),
        wait=wait_exponential(multiplier=0.5, max=4.0),
        retry=retry_if_exception_type((ccxt.NetworkError, ccxt.ExchangeNotAvailable)),
    )
    def _call() -> list[list[float]]:
        return client.fetch_ohlcv(symbol, interval, limit=limit)

    try:
        return _call()
    except ccxt.BadSymbol as exc:
        raise UpstreamFetchError(f"unknown symbol: {symbol}") from exc
    except ccxt.BaseError as exc:
        logger.warning("ccxt_fetch_failed", exchange=exchange, symbol=symbol, error=str(exc))
        raise UpstreamFetchError("upstream exchange error") from exc
    except RetryError as exc:
        logger.warning("ccxt_retry_exhausted", exchange=exchange, symbol=symbol)
        raise UpstreamFetchError("upstream exchange unavailable") from exc


def reset_client_cache() -> None:
    get_exchange_client.cache_clear()
