# Indicators API
Binance API indicators (ADX, RSI, MINUS_DI and PLUS_DI)

**List containers:**

``sudo docker ps -a``

**Build container**

``sudo docker build --no-cache . -t indicators``

**Run container**

``sudo docker run -it --rm -p 5000:5000 indicators``

**Get indicators**

http://localhost:5000/?symbol=BTCUSDT&interval=5m

**Suported params**

*symbol*: ‘BTCUSDT’ Bitcoin to Tether, or LTCBTC Litecoin to Bitcoin.

*interval*: Binance have the following time frames or intervals: ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M'].

**Example response**

```json
  {
    "adx": 14.625980895238811,
    "minus_di": 20.056506186367354,
    "plus_di": 20.41933578565063,
    "rsi": 47.763117632729035
  }
```
