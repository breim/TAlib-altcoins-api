from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from talib_altcoins_api.api.indicators import limiter, reset_response_cache
from talib_altcoins_api.core.config import reset_settings_cache
from talib_altcoins_api.core.exchanges import UnknownExchangeError, UpstreamFetchError


@pytest.fixture
def _patch_fetch(monkeypatch: pytest.MonkeyPatch, ohlcv: list[list[float]]) -> None:
    def _fake(exchange: str, symbol: str, interval: str, limit: int) -> list[list[float]]:
        return ohlcv[-limit:]

    monkeypatch.setattr("talib_altcoins_api.api.indicators.fetch_ohlcv", _fake)


@pytest.mark.usefixtures("_patch_fetch")
def test_indicators_happy_path(client: TestClient) -> None:
    response = client.get(
        "/indicators",
        params={"exchange": "binance", "symbol": "BTC/USDT", "interval": "1h", "limit": 200},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    expected_keys = {
        "adx",
        "rsi",
        "plus_di",
        "minus_di",
        "sma",
        "sma_5",
        "sma_10",
        "sma_dir",
        "macd",
        "macdsignal",
        "ma_50",
        "ma_100",
        "rsi_obv",
        "linear_regression",
        "linear_angle",
        "linear_intercept",
        "linear_slope",
    }
    assert set(body.keys()) == expected_keys


def test_unknown_exchange_returns_404(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(*_a: object, **_kw: object) -> list[list[float]]:
        raise UnknownExchangeError("fakeexchange")

    monkeypatch.setattr("talib_altcoins_api.api.indicators.fetch_ohlcv", _raise)
    response = client.get(
        "/indicators",
        params={"exchange": "fakeexchange", "symbol": "BTC/USDT", "interval": "1h"},
    )
    assert response.status_code == 404


def test_upstream_failure_returns_502(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(*_a: object, **_kw: object) -> list[list[float]]:
        raise UpstreamFetchError("upstream exchange error")

    monkeypatch.setattr("talib_altcoins_api.api.indicators.fetch_ohlcv", _raise)
    response = client.get(
        "/indicators",
        params={"exchange": "binance", "symbol": "BTC/USDT", "interval": "1h"},
    )
    assert response.status_code == 502


def test_bad_symbol_format_returns_422(client: TestClient) -> None:
    response = client.get(
        "/indicators",
        params={"exchange": "binance", "symbol": "BTCUSDT", "interval": "1h"},
    )
    assert response.status_code == 422


def test_limit_too_high_returns_422(client: TestClient) -> None:
    response = client.get(
        "/indicators",
        params={"exchange": "binance", "symbol": "BTC/USDT", "interval": "1h", "limit": 999999},
    )
    assert response.status_code == 422


def test_invalid_interval_returns_422(client: TestClient) -> None:
    response = client.get(
        "/indicators",
        params={"exchange": "binance", "symbol": "BTC/USDT", "interval": "9d"},
    )
    assert response.status_code == 422


def test_insufficient_data_returns_422(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, ohlcv: list[list[float]]
) -> None:
    def _fake(*_a: object, **_kw: object) -> list[list[float]]:
        return ohlcv[:50]

    monkeypatch.setattr("talib_altcoins_api.api.indicators.fetch_ohlcv", _fake)
    response = client.get(
        "/indicators",
        params={"exchange": "binance", "symbol": "BTC/USDT", "interval": "1h", "limit": 200},
    )
    assert response.status_code == 422


@pytest.mark.parametrize("name", ["exchanges", "errors", "base", "decimal_to_precision"])
def test_ccxt_module_attribute_returns_404_not_500(client: TestClient, name: str) -> None:
    response = client.get(
        "/indicators",
        params={"exchange": name, "symbol": "BTC/USDT", "interval": "1h"},
    )
    assert response.status_code == 404, response.text


@pytest.mark.usefixtures("_patch_fetch")
def test_rate_limit_exceeded_returns_429(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("RATE_LIMIT", "2/minute")
    reset_settings_cache()
    limiter.reset()

    params = {"exchange": "binance", "symbol": "BTC/USDT", "interval": "1h"}
    statuses = [client.get("/indicators", params=params).status_code for _ in range(4)]

    assert statuses[:2] == [200, 200]
    assert statuses[2:] == [429, 429]

    limiter.reset()


@pytest.mark.usefixtures("_patch_fetch")
def test_repeated_request_is_served_from_cache(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, ohlcv: list[list[float]]
) -> None:
    monkeypatch.setenv("CACHE_TTL_SECONDS", "60")
    reset_settings_cache()
    reset_response_cache()

    calls = {"n": 0}

    def _counting(*_a: object, **_kw: object) -> list[list[float]]:
        calls["n"] += 1
        return ohlcv

    monkeypatch.setattr("talib_altcoins_api.api.indicators.fetch_ohlcv", _counting)

    params: dict[str, str | int] = {
        "exchange": "binance",
        "symbol": "BTC/USDT",
        "interval": "1h",
        "limit": 200,
    }
    first = client.get("/indicators", params=params)
    second = client.get("/indicators", params=params)

    assert first.status_code == 200
    assert second.json() == first.json()
    assert calls["n"] == 1
