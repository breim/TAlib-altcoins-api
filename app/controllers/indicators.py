import talib
import ccxt
import numpy as np
import pandas as pd

from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.get('/indicators')
async def indicators(exchange: str, symbol: str, interval: str = '30m', limit: int = 100):
    try:
        exchange_client = getattr(ccxt, exchange)()
    except AttributeError:
        raise HTTPException(status_code=404, detail=f"Exchange {exchange} not found.")

    try:
        kline = exchange_client.fetch_ohlcv(symbol, interval, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    df = pd.DataFrame(kline, columns=['time', 'open', 'high', 'low', 'close', 'volume']).astype('float64')

    indicators = calculate_indicators(df)
    return indicators

def calculate_indicators(df):
    adx = talib.ADX(df['high'], df['low'], df['close'], timeperiod=14)[-1]
    rsi = talib.RSI(df['close'], timeperiod=14)[-1]
    plus_di = talib.PLUS_DI(df['high'], df['low'], df['close'], timeperiod=14)[-1]
    minus_di = talib.MINUS_DI(df['high'], df['low'], df['close'], timeperiod=14)[-1]
    sma = talib.SMA(df['close'], timeperiod=30)[-1]
    sma_5 = talib.SMA(df['close'], timeperiod=5)[-1]
    sma_10 = talib.SMA(df['close'], timeperiod=10)[-1]
    sma_dir = round(sma - sma_10, 8)
    macd, macdsignal, _ = talib.MACD(df['close'], fastperiod=12, slowperiod=26, signalperiod=9)
    obv = talib.OBV(df['close'], df['volume'])

    return {
        "adx": adx,
        "rsi": rsi,
        "plus_di": plus_di,
        "minus_di": minus_di,
        "sma": round(sma, 8),
        "sma_10": round(sma_10, 8),
        "sma_5": round(sma_5, 8),
        "sma_dir": sma_dir,
        "macd": macd[-1],
        "macdsignal": macdsignal[-1],
        "ma_50": talib.MA(df['close'], timeperiod=50)[-1],
        "ma_100": talib.MA(df['close'], timeperiod=100)[-1],
        "rsi_obv": talib.RSI(obv, timeperiod=14)[-1],
        "linear_regression": talib.LINEARREG(df['close'], timeperiod=14)[-1],
        "linear_angle": talib.LINEARREG_ANGLE(df['close'], timeperiod=14)[-1],
        "linear_intercept": talib.LINEARREG_INTERCEPT(df['close'], timeperiod=14)[-1],
        "linear_slope": talib.LINEARREG_SLOPE(df['close'], timeperiod=14)[-1]
    }
