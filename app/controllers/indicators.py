import talib
import ccxt
import requests
import numpy as np
import pandas as pd
from datetime import datetime
from app import app
from fastapi import Request
  
@app.get('/indicators')
async def indicators(exchange: str, symbol: str, interval: str = '30m', limit: int = 100):
    exchange = getattr(ccxt, exchange)()
    kline = exchange.fetch_ohlcv(symbol, interval, limit=int(limit))

    df = pd.DataFrame(np.array(kline),
                       columns=['open_time', 'open', 'high', 'low', 'close', 'volume'],
                       dtype='float64')

    op = df['open']
    hi = df['high']
    lo = df['low']
    cl = df['close']
    vl = df['volume']

    adx = talib.ADX(hi.values, lo.values, cl.values, timeperiod=14)
    rsi = talib.RSI(cl.values, timeperiod=14)
    plus_di = talib.PLUS_DI(hi.values, lo.values, cl.values, timeperiod=14)
    minus_di = talib.MINUS_DI(hi.values, lo.values, cl.values, timeperiod=14)
    sma = talib.SMA(cl.values, timeperiod=30)
    sma_5 = talib.SMA(cl.values, timeperiod=5)
    sma_10 = talib.SMA(cl.values, timeperiod=10)
    sma_dir = convert_number(round(sma[-1], 8) - round(sma_10[-1], 8))
    macd, macdsignal, macdhist = talib.MACD(cl.values, fastperiod=12, slowperiod=26, signalperiod=14)    
    macd = convert_number(macd[-1])
    macdsignal = convert_number(macdsignal[-1])
    ma_50 = convert_number(talib.MA(cl.values, timeperiod=50, matype=0)[-1])
    ma_100 = convert_number(talib.MA(cl.values, timeperiod=100, matype=0)[-1])
    obv = talib.OBV(cl.values, vl.values)
    rsi_obv = convert_number(talib.RSI(obv, timeperiod=14)[-1])
    linear_regression = talib.LINEARREG(cl.values, timeperiod=14)[-1]
    linear_angle =  convert_number(talib.LINEARREG_ANGLE(cl.values, timeperiod=14)[-1])
    linear_intercept = convert_number(talib.LINEARREG_INTERCEPT(cl.values, timeperiod=14)[-1])
    linear_slope = convert_number(talib.LINEARREG_SLOPE(cl.values, timeperiod=14)[-1])
    
    return {
      "adx": adx[-1],
      "rsi": rsi[-1],
      "plus_di": plus_di[-1],
      "minus_di": minus_di[-1],
      "sma": round(sma[-1], 8),
      "sma_10": round(sma_10[-1], 8),
      "sma_5": round(sma_5[-1], 8),
      "sma_dir": sma_dir,
      "macd": macd,
      "macdsignal": macdsignal,
      "ma_50": ma_50,
      "ma_100": ma_100,
      "rsi_obv": rsi_obv,
      "linear_regression": linear_regression,
      "linear_angle": linear_angle,
      "linear_intercept": linear_intercept,
      "linear_slope": linear_slope
    }

def convert_number(value):
    return (float(str(float(np.format_float_scientific(value, unique=False, precision=8))).split('e-')[0]))