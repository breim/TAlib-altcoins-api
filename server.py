import talib
import requests
import numpy as np
import pandas as pd
from datetime import datetime
from flask import Flask, jsonify, request

app = Flask(__name__)

# http://localhost:5000?symbol=BTCUSDT&interval=5m
@app.route("/")
def indicators():
    symbol = request.args.get('symbol')
    interval = request.args.get('interval')
    historical_json = requests.get(f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}').json()

    df = pd.DataFrame(np.array(historical_json),
                       columns=['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_volume', 'taker_buy_quota_volume', 'ignore'],
                       dtype='float')

    op = df['open']
    hi = df['high']
    lo = df['low']
    cl = df['close']

    adx = talib.ADX(hi.values, lo.values, cl.values, timeperiod=14)
    rsi = talib.RSI(cl.values, timeperiod=14)
    plus_di = talib.PLUS_DI(hi.values, lo.values, cl.values, timeperiod=14)
    minus_di = talib.MINUS_DI(hi.values, lo.values, cl.values, timeperiod=14)

    return jsonify(
      adx=adx[-1],
      rsi=rsi[-1],
      plus_di=plus_di[-1],
      minus_di=minus_di[-1]
    )

if __name__ == '__main__':
    app.run(debug=True)