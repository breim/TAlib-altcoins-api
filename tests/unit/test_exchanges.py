from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor

import ccxt
import pytest

from talib_altcoins_api.core.config import reset_settings_cache
from talib_altcoins_api.core.exchanges import (
    CachedExchange,
    UnknownExchangeError,
    UpstreamFetchError,
    fetch_ohlcv,
    get_exchange_client,
    reset_client_cache,
)

OHLCV_ROW = [[1.0, 2.0, 3.0, 4.0, 5.0, 6.0]]


@pytest.fixture(autouse=True)
def _clean_caches() -> None:
    reset_client_cache()
    reset_settings_cache()


class _FakeClient:
    def __init__(self, *errors: Exception) -> None:
        self.errors = list(errors)
        self.calls = 0

    def fetch_ohlcv(
        self, symbol: str, timeframe: str, since: int | None = None, limit: int | None = None
    ) -> list[list[float]]:
        self.calls += 1
        if self.errors:
            raise self.errors.pop(0)
        return OHLCV_ROW


def _install(monkeypatch: pytest.MonkeyPatch, client: object) -> None:
    cached = CachedExchange(client=client, lock=threading.Lock())  # type: ignore[arg-type]
    monkeypatch.setattr(
        "talib_altcoins_api.core.exchanges.get_exchange_client", lambda _name: cached
    )


@pytest.mark.parametrize("name", ["exchanges", "errors", "base", "decimal_to_precision"])
def test_ccxt_module_attributes_are_not_exchanges(name: str) -> None:
    assert hasattr(ccxt, name)
    with pytest.raises(UnknownExchangeError):
        get_exchange_client(name)


def test_unknown_exchange_name_raises() -> None:
    with pytest.raises(UnknownExchangeError):
        get_exchange_client("definitely_not_an_exchange")


def test_known_exchange_returns_client_and_lock() -> None:
    cached = get_exchange_client("binance")
    assert hasattr(cached.client, "fetch_ohlcv")
    assert isinstance(cached.lock, threading.Lock)


def test_client_is_cached_per_exchange() -> None:
    assert get_exchange_client("binance") is get_exchange_client("binance")


def test_bad_symbol_maps_to_upstream_error(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(monkeypatch, _FakeClient(ccxt.BadSymbol("nope")))
    with pytest.raises(UpstreamFetchError, match="unknown symbol: BTC/USDT"):
        fetch_ohlcv("binance", "BTC/USDT", "1h", 200)


def test_generic_ccxt_error_maps_to_upstream_error(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(monkeypatch, _FakeClient(ccxt.ExchangeError("boom")))
    with pytest.raises(UpstreamFetchError, match="upstream exchange error"):
        fetch_ohlcv("binance", "BTC/USDT", "1h", 200)


def test_network_error_is_retried_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CCXT_MAX_RETRIES", "2")
    reset_settings_cache()
    client = _FakeClient(ccxt.NetworkError("flaky"))
    _install(monkeypatch, client)

    assert fetch_ohlcv("binance", "BTC/USDT", "1h", 200) == OHLCV_ROW
    assert client.calls == 2


def test_retry_exhaustion_maps_to_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CCXT_MAX_RETRIES", "1")
    reset_settings_cache()
    client = _FakeClient(ccxt.NetworkError("down"), ccxt.NetworkError("down"))
    _install(monkeypatch, client)

    with pytest.raises(UpstreamFetchError, match="upstream exchange unavailable"):
        fetch_ohlcv("binance", "BTC/USDT", "1h", 200)
    assert client.calls == 2


def test_bad_symbol_is_not_retried(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CCXT_MAX_RETRIES", "3")
    reset_settings_cache()
    client = _FakeClient(ccxt.BadSymbol("nope"))
    _install(monkeypatch, client)

    with pytest.raises(UpstreamFetchError):
        fetch_ohlcv("binance", "BTC/USDT", "1h", 200)
    assert client.calls == 1


def test_concurrent_calls_do_not_share_client_unserialised(monkeypatch: pytest.MonkeyPatch) -> None:
    barrier_state = {"active": 0, "max_active": 0}
    state_lock = threading.Lock()

    class _ConcurrencyProbe:
        def fetch_ohlcv(
            self, symbol: str, timeframe: str, since: int | None = None, limit: int | None = None
        ) -> list[list[float]]:
            with state_lock:
                barrier_state["active"] += 1
                barrier_state["max_active"] = max(
                    barrier_state["max_active"], barrier_state["active"]
                )
            try:
                threading.Event().wait(0.01)
                return OHLCV_ROW
            finally:
                with state_lock:
                    barrier_state["active"] -= 1

    _install(monkeypatch, _ConcurrencyProbe())

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: fetch_ohlcv("binance", "BTC/USDT", "1h", 200), range(16)))

    assert all(r == OHLCV_ROW for r in results)
    assert barrier_state["max_active"] == 1
