from __future__ import annotations

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from talib_altcoins_api.api.health import router as health_router
from talib_altcoins_api.api.indicators import limiter as indicators_limiter
from talib_altcoins_api.api.indicators import rate_limit_handler
from talib_altcoins_api.api.indicators import router as indicators_router
from talib_altcoins_api.core.config import get_settings
from talib_altcoins_api.core.logging import configure_logging
from talib_altcoins_api.core.sentry import configure_sentry


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)
    configure_sentry(settings)

    app = FastAPI(
        title="TA-Lib Altcoins API",
        version="0.1.0",
        description="Technical indicators over OHLCV data fetched from crypto exchanges.",
    )

    app.state.limiter = indicators_limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
    app.add_middleware(SlowAPIMiddleware)

    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(indicators_router)

    Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

    return app


app = create_app()
