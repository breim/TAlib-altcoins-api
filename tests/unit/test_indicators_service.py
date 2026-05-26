from __future__ import annotations

import math

import pytest

from talib_altcoins_api.schemas.indicators import IndicatorParams
from talib_altcoins_api.services.indicators import (
    InsufficientDataError,
    calculate_indicators,
    ohlcv_to_dataframe,
)


def _default_params() -> IndicatorParams:
    return IndicatorParams(
        adx_period=14,
        rsi_period=14,
        sma_short_period=5,
        sma_mid_period=10,
        sma_long_period=30,
        ma_50_period=50,
        ma_100_period=100,
        macd_fast=12,
        macd_slow=26,
        macd_signal=9,
        linear_reg_period=14,
    )


def test_calculate_returns_finite_values(ohlcv: list[list[float]]) -> None:
    df = ohlcv_to_dataframe(ohlcv)
    response = calculate_indicators(df, _default_params())
    values = response.model_dump()
    for name, value in values.items():
        assert math.isfinite(value), f"{name} is not finite: {value}"


def test_insufficient_data_raises(ohlcv: list[list[float]]) -> None:
    df = ohlcv_to_dataframe(ohlcv[:20])
    with pytest.raises(InsufficientDataError) as excinfo:
        calculate_indicators(df, _default_params())
    assert excinfo.value.have == 20
    assert excinfo.value.need > 20


def test_zero_rows_raises() -> None:
    df = ohlcv_to_dataframe([])
    with pytest.raises(InsufficientDataError):
        calculate_indicators(df, _default_params())


def test_sma_dir_is_long_minus_mid(ohlcv: list[list[float]]) -> None:
    df = ohlcv_to_dataframe(ohlcv)
    response = calculate_indicators(df, _default_params())
    assert response.sma_dir == pytest.approx(response.sma - response.sma_10, rel=1e-9)
