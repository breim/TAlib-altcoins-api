import talib
import ccxt
import requests
import numpy as np
import pandas as pd
from datetime import datetime
from flask import jsonify, request

from __main__ import app

@app.route('/indicators', methods=['GET'])
def indicators():
    exchange_symbol = request.args.get('exchange')
    symbol = request.args.get('symbol')
    interval = request.args.get('interval', '30m')
    limit = request.args.get('limit', 100)

    exchange = getattr(ccxt, exchange_symbol)()
    kline = exchange.fetch_ohlcv(symbol, interval, limit=int(limit))

    df = pd.DataFrame(np.array(kline),
                       columns=['open_time', 'open', 'high', 'low', 'close', 'volume'],
                       dtype='float64')

    op = df['open']
    hi = df['high']
    lo = df['low']
    cl = df['close']

    adx = talib.ADX(hi.values, lo.values, cl.values, timeperiod=14)
    rsi = talib.RSI(cl.values, timeperiod=14)
    plus_di = talib.PLUS_DI(hi.values, lo.values, cl.values, timeperiod=14)
    minus_di = talib.MINUS_DI(hi.values, lo.values, cl.values, timeperiod=14)
    sma = talib.SMA(cl.values, timeperiod=5)
    macd, macdsignal, macdhist = talib.MACD(cl.values, fastperiod=12, slowperiod=26, signalperiod=14)    
    macd = convert_number(macd[-1])
    ma_50 = convert_number(talib.MA(cl.values, timeperiod=50, matype=0)[-1])
    ma_100 = convert_number(talib.MA(cl.values, timeperiod=100, matype=0)[-1])
     
    return jsonify(
      adx = adx[-1],
      rsi = rsi[-1],
      plus_di = plus_di[-1],
      minus_di = minus_di[-1],
      sma = round(sma[-1], 8),
      macd = macd,
      ma_50 = ma_50,
      ma_100 = ma_100
    )

def convert_number(value):
    return (float(str(float(np.format_float_scientific(value, unique=False, precision=2))).split('e-')[0]))
