import talib
import requests
import numpy as np
import pandas as pd
from datetime import datetime
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route("/")
def indicators():
    symbol = request.args.get('symbol')
    interval = request.args.get('interval')
    historical_json = requests.get(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}').json()

    df = pd.DataFrame(np.array(historical_json),
                       columns=['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_volume', 'taker_buy_quota_volume', 'ignore'],
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
    macd = convert_macd(macd[-1])
     
    return jsonify(
      adx=adx[-1],
      rsi=rsi[-1],
      plus_di=plus_di[-1],
      minus_di=minus_di[-1],
      sma=round(sma[-1], 8),
      macd=macd
    )

def convert_macd(value):
    return (float(str(float(np.format_float_scientific(value, unique=False, precision=2))).split('e-')[0]))

if __name__ == '__main__':
    print("Example: http://localhost:5000?symbol=BTCUSDT&interval=5m")
    app.run(host='0.0.0.0', debug=True)