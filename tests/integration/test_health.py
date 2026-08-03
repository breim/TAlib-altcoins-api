from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from talib_altcoins_api.core.config import reset_settings_cache


def test_root(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"docs": "/docs", "health": "/healthz"}


def test_healthz(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readyz(client: TestClient) -> None:
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_metrics_exposed_by_default(client: TestClient) -> None:
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "# HELP" in response.text


@pytest.mark.usefixtures("_reset_caches")
def test_metrics_can_be_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("METRICS_ENABLED", "false")
    reset_settings_cache()

    from talib_altcoins_api.main import create_app

    with TestClient(create_app()) as disabled_client:
        assert disabled_client.get("/metrics").status_code == 404
        assert disabled_client.get("/healthz").status_code == 200
