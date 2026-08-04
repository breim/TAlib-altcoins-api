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


class IndicatorUnstableError(ValueError):
    def __init__(self, indicator: str, rows: int) -> None:
        super().__init__(
            f"{indicator} produced no finite value over {rows} rows; retry with a larger limit"
        )
        self.indicator = indicator
        self.rows = rows


OHLCV_COLUMNS = ("time", "open", "high", "low", "close", "volume")


def ohlcv_to_dataframe(rows: Iterable[Iterable[float]]) -> pd.DataFrame:
    df = pd.DataFrame(list(rows), columns=list(OHLCV_COLUMNS))
    return df.astype("float64")


def _required_rows(params: IndicatorParams) -> int:
    return max(
        params.adx_period * 2,
        params.rsi_period + 1,
        params.sma_short_period,
        params.sma_mid_period,
        params.sma_long_period,
        params.ma_50_period,
        params.ma_100_period,
        max(params.macd_fast, params.macd_slow) + params.macd_signal,
        params.linear_reg_period,
    )


def _last_finite(values: np.ndarray, indicator: str) -> float:
    value = float(values[-1])
    if not math.isfinite(value):
        raise IndicatorUnstableError(indicator=indicator, rows=int(values.size))
    return value


def calculate_indicators(df: pd.DataFrame, params: IndicatorParams) -> IndicatorResponse:
    needed = _required_rows(params)
    if len(df) < needed:
        raise InsufficientDataError(have=len(df), need=needed)

    high = df["high"].to_numpy(dtype=np.float64)
    low = df["low"].to_numpy(dtype=np.float64)
    close = df["close"].to_numpy(dtype=np.float64)
    volume = df["volume"].to_numpy(dtype=np.float64)

    adx = _last_finite(talib.ADX(high, low, close, timeperiod=params.adx_period), "ADX")
    plus_di = _last_finite(talib.PLUS_DI(high, low, close, timeperiod=params.adx_period), "PLUS_DI")
    minus_di = _last_finite(
        talib.MINUS_DI(high, low, close, timeperiod=params.adx_period), "MINUS_DI"
    )
    rsi = _last_finite(talib.RSI(close, timeperiod=params.rsi_period), "RSI")

    sma_long = _last_finite(talib.SMA(close, timeperiod=params.sma_long_period), "SMA")
    sma_mid = _last_finite(talib.SMA(close, timeperiod=params.sma_mid_period), "SMA_10")
    sma_short = _last_finite(talib.SMA(close, timeperiod=params.sma_short_period), "SMA_5")

    macd_arr, macdsignal_arr, _ = talib.MACD(
        close,
        fastperiod=params.macd_fast,
        slowperiod=params.macd_slow,
        signalperiod=params.macd_signal,
    )
    macd = _last_finite(macd_arr, "MACD")
    macdsignal = _last_finite(macdsignal_arr, "MACD_SIGNAL")

    ma_50 = _last_finite(talib.MA(close, timeperiod=params.ma_50_period), "MA_50")
    ma_100 = _last_finite(talib.MA(close, timeperiod=params.ma_100_period), "MA_100")

    obv = talib.OBV(close, volume)
    rsi_obv = _last_finite(talib.RSI(obv, timeperiod=params.rsi_period), "RSI_OBV")

    p = params.linear_reg_period
    linear_regression = _last_finite(talib.LINEARREG(close, timeperiod=p), "LINEARREG")
    linear_angle = _last_finite(talib.LINEARREG_ANGLE(close, timeperiod=p), "LINEARREG_ANGLE")
    linear_intercept = _last_finite(
        talib.LINEARREG_INTERCEPT(close, timeperiod=p), "LINEARREG_INTERCEPT"
    )
    linear_slope = _last_finite(talib.LINEARREG_SLOPE(close, timeperiod=p), "LINEARREG_SLOPE")

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
