from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Interval = Literal[
    "1m",
    "3m",
    "5m",
    "15m",
    "30m",
    "1h",
    "2h",
    "4h",
    "6h",
    "8h",
    "12h",
    "1d",
    "3d",
    "1w",
    "1M",
]


class IndicatorParams(BaseModel):
    model_config = ConfigDict(frozen=True)

    adx_period: int
    rsi_period: int
    sma_short_period: int
    sma_mid_period: int
    sma_long_period: int
    ma_50_period: int
    ma_100_period: int
    macd_fast: int
    macd_slow: int
    macd_signal: int
    linear_reg_period: int


class IndicatorResponse(BaseModel):
    adx: float
    rsi: float
    plus_di: float
    minus_di: float
    sma: float
    sma_5: float
    sma_10: float
    sma_dir: float
    macd: float
    macdsignal: float
    ma_50: float
    ma_100: float
    rsi_obv: float
    linear_regression: float
    linear_angle: float
    linear_intercept: float
    linear_slope: float


class ErrorResponse(BaseModel):
    detail: str = Field(..., examples=["upstream exchange error"])
