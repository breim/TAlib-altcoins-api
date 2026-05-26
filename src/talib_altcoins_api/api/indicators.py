from __future__ import annotations

import re
from typing import Annotated

import anyio
import structlog
from cachetools import TTLCache
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from talib_altcoins_api.core.config import Settings, get_settings
from talib_altcoins_api.core.exchanges import (
    UnknownExchangeError,
    UpstreamFetchError,
    fetch_ohlcv,
)
from talib_altcoins_api.schemas.indicators import (
    ErrorResponse,
    IndicatorParams,
    IndicatorResponse,
    Interval,
)
from talib_altcoins_api.services.indicators import (
    InsufficientDataError,
    calculate_indicators,
    ohlcv_to_dataframe,
)

logger = structlog.get_logger(__name__)

_SYMBOL_RE = re.compile(r"^[A-Z0-9]{2,10}/[A-Z0-9]{2,10}$")
_CACHE: TTLCache[tuple[str, str, str, int], IndicatorResponse] = TTLCache(maxsize=512, ttl=30)


def _settings_rate_limit_key() -> str:
    return get_settings().rate_limit


limiter = Limiter(key_func=get_remote_address, default_limits=[])


def rate_limit_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RateLimitExceeded)
    return JSONResponse(status_code=429, content={"detail": "rate limit exceeded"})


def _params_from_settings(settings: Settings) -> IndicatorParams:
    return IndicatorParams(
        adx_period=settings.adx_period,
        rsi_period=settings.rsi_period,
        sma_short_period=settings.sma_short_period,
        sma_mid_period=settings.sma_mid_period,
        sma_long_period=settings.sma_long_period,
        ma_50_period=settings.ma_50_period,
        ma_100_period=settings.ma_100_period,
        macd_fast=settings.macd_fast,
        macd_slow=settings.macd_slow,
        macd_signal=settings.macd_signal,
        linear_reg_period=settings.linear_reg_period,
    )


router = APIRouter(tags=["indicators"])


@router.get(
    "/indicators",
    response_model=IndicatorResponse,
    responses={
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
    },
)
@limiter.limit(_settings_rate_limit_key)
async def get_indicators(
    request: Request,
    exchange: Annotated[str, Query(min_length=2, max_length=40, pattern=r"^[a-z0-9_]+$")],
    symbol: Annotated[str, Query(min_length=5, max_length=21)],
    settings: Annotated[Settings, Depends(get_settings)],
    interval: Interval = "30m",
    limit: Annotated[int, Query(ge=50, le=1000)] = 200,
) -> IndicatorResponse:
    if not _SYMBOL_RE.match(symbol):
        raise HTTPException(status_code=422, detail="symbol must look like 'BTC/USDT'")

    cache_key = (exchange, symbol, interval, limit)
    cached = _CACHE.get(cache_key)
    if cached is not None:
        return cached

    if _CACHE.ttl != settings.cache_ttl_seconds:
        _CACHE.clear()
        _CACHE.__init__(maxsize=512, ttl=settings.cache_ttl_seconds)  # type: ignore[misc]

    try:
        rows = await anyio.to_thread.run_sync(fetch_ohlcv, exchange, symbol, interval, limit)
    except UnknownExchangeError as exc:
        raise HTTPException(status_code=404, detail=f"exchange {exc} not found") from exc
    except UpstreamFetchError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    df = ohlcv_to_dataframe(rows)
    params = _params_from_settings(settings)

    try:
        result = calculate_indicators(df, params)
    except InsufficientDataError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    _CACHE[cache_key] = result
    return result
