from __future__ import annotations

import os
from collections.abc import Iterator

import numpy as np
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("LOG_JSON", "false")
    monkeypatch.setenv("RATE_LIMIT", "10000/minute")
    monkeypatch.setenv("CACHE_TTL_SECONDS", "0")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "")
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    os.environ.pop("DOTENV_PATH", None)


@pytest.fixture
def _reset_caches() -> Iterator[None]:
    from talib_altcoins_api.api.indicators import reset_response_cache
    from talib_altcoins_api.core.config import reset_settings_cache
    from talib_altcoins_api.core.exchanges import reset_client_cache

    reset_settings_cache()
    reset_client_cache()
    reset_response_cache()
    yield
    reset_settings_cache()
    reset_client_cache()
    reset_response_cache()


@pytest.fixture
def ohlcv() -> list[list[float]]:
    rng = np.random.default_rng(42)
    n = 250
    returns = rng.normal(0.0, 0.01, size=n)
    close = 100.0 * np.exp(np.cumsum(returns))
    open_ = np.concatenate(([100.0], close[:-1]))
    high = np.maximum(open_, close) * (1 + np.abs(rng.normal(0, 0.002, size=n)))
    low = np.minimum(open_, close) * (1 - np.abs(rng.normal(0, 0.002, size=n)))
    volume = rng.uniform(10.0, 100.0, size=n)
    rows = []
    for i in range(n):
        rows.append(
            [
                float(i),
                float(open_[i]),
                float(high[i]),
                float(low[i]),
                float(close[i]),
                float(volume[i]),
            ]
        )
    return rows


@pytest.fixture
def client(_reset_caches: None) -> Iterator[TestClient]:
    from talib_altcoins_api.main import create_app

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
