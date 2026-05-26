from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

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
