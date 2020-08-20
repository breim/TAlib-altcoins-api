# Exchanges API with ta-lib indicators

**List containers:**

``sudo docker ps -a``

**Build container**

``sudo docker build --no-cache . -t indicators``

**Run container**

``sudo docker run -it --rm -p 5000:5000 indicators``

**Get indicators**

http://localhost:5000/indicators?exchange=binance&symbol=BTC/USDT&interval=1h

**Suported params**

*exchange*: [supported list](https://github.com/ccxt/ccxt#supported-cryptocurrency-exchange-markets)

*symbol*: ‘BTC/USDT’ Bitcoin to Tether, or LTCBTC Litecoin to Bitcoin.

*interval*: Binance have the following time frames or intervals: ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M'].

*limit*: Limit binance api return default is 100

**Example response**

```json
  {
    "adx": 52.90973494613487,
    "ma_100": 11700,
    "ma_50": 11700,
    "macd": -30.9,
    "minus_di": 39.19350254139547,
    "plus_di": 4.528784884053814,
    "rsi": 33.51984340870133,
    "sma": 11607.09
  }
```
