from __future__ import annotations

import pytest

from talib_altcoins_api.core.config import Settings, reset_settings_cache


def test_defaults() -> None:
    reset_settings_cache()
    settings = Settings()
    assert settings.host == "0.0.0.0"
    assert settings.port == 5001
    assert settings.adx_period == 14
    assert settings.cors_allow_origins == []


def test_cors_csv_parsing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "https://a.example, https://b.example")
    settings = Settings()
    assert settings.cors_allow_origins == ["https://a.example", "https://b.example"]


def test_period_bounds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ADX_PERIOD", "1")
    with pytest.raises(ValueError, match="adx_period"):
        Settings()


def test_port_bounds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PORT", "0")
    with pytest.raises(ValueError, match="port"):
        Settings()
