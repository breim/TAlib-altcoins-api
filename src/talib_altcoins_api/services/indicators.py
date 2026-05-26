from __future__ import annotations

import math
from collections.abc import Iterable

import numpy as np
import pandas as pd
import talib

from talib_altcoins_api.schemas.indicators import IndicatorParams, IndicatorResponse


class InsufficientDataError(ValueError):
    def __init__(self, have: int, need: int) -> None:
        super().__init__(f"need at least {need} OHLCV rows, got {have}")
        self.have = have
        self.need = need


OHLCV_COLUMNS = ("time", "open", "high", "low", "close", "volume")


def ohlcv_to_dataframe(rows: Iterable[Iterable[float]]) -> pd.DataFrame:
    df = pd.DataFrame(list(rows), columns=list(OHLCV_COLUMNS))
    return df.astype("float64")


def _required_rows(params: IndicatorParams) -> int:
    return max(
        params.adx_period * 2,
        params.rsi_period + 1,
        params.sma_long_period,
        params.ma_50_period,
        params.ma_100_period,
        params.macd_slow + params.macd_signal,
        params.linear_reg_period,
    )


def _last_finite(values: np.ndarray) -> float:
    if values.size == 0:
        raise InsufficientDataError(have=0, need=1)
    value = float(values[-1])
    if not math.isfinite(value):
        raise InsufficientDataError(have=int(values.size), need=int(values.size) + 1)
    return value


def calculate_indicators(df: pd.DataFrame, params: IndicatorParams) -> IndicatorResponse:
    needed = _required_rows(params)
    if len(df) < needed:
        raise InsufficientDataError(have=len(df), need=needed)

    high = df["high"].to_numpy(dtype=np.float64)
    low = df["low"].to_numpy(dtype=np.float64)
    close = df["close"].to_numpy(dtype=np.float64)
    volume = df["volume"].to_numpy(dtype=np.float64)

    adx = _last_finite(talib.ADX(high, low, close, timeperiod=params.adx_period))
    plus_di = _last_finite(talib.PLUS_DI(high, low, close, timeperiod=params.adx_period))
    minus_di = _last_finite(talib.MINUS_DI(high, low, close, timeperiod=params.adx_period))
    rsi = _last_finite(talib.RSI(close, timeperiod=params.rsi_period))

    sma_long = _last_finite(talib.SMA(close, timeperiod=params.sma_long_period))
    sma_mid = _last_finite(talib.SMA(close, timeperiod=params.sma_mid_period))
    sma_short = _last_finite(talib.SMA(close, timeperiod=params.sma_short_period))

    macd_arr, macdsignal_arr, _ = talib.MACD(
        close,
        fastperiod=params.macd_fast,
        slowperiod=params.macd_slow,
        signalperiod=params.macd_signal,
    )
    macd = _last_finite(macd_arr)
    macdsignal = _last_finite(macdsignal_arr)

    ma_50 = _last_finite(talib.MA(close, timeperiod=params.ma_50_period))
    ma_100 = _last_finite(talib.MA(close, timeperiod=params.ma_100_period))

    obv = talib.OBV(close, volume)
    rsi_obv = _last_finite(talib.RSI(obv, timeperiod=params.rsi_period))

    p = params.linear_reg_period
    linear_regression = _last_finite(talib.LINEARREG(close, timeperiod=p))
    linear_angle = _last_finite(talib.LINEARREG_ANGLE(close, timeperiod=p))
    linear_intercept = _last_finite(talib.LINEARREG_INTERCEPT(close, timeperiod=p))
    linear_slope = _last_finite(talib.LINEARREG_SLOPE(close, timeperiod=p))

    return IndicatorResponse(
        adx=adx,
        rsi=rsi,
        plus_di=plus_di,
        minus_di=minus_di,
        sma=sma_long,
        sma_5=sma_short,
        sma_10=sma_mid,
        sma_dir=sma_long - sma_mid,
        macd=macd,
        macdsignal=macdsignal,
        ma_50=ma_50,
        ma_100=ma_100,
        rsi_obv=rsi_obv,
        linear_regression=linear_regression,
        linear_angle=linear_angle,
        linear_intercept=linear_intercept,
        linear_slope=linear_slope,
    )
