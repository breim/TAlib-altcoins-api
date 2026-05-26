from __future__ import annotations

import uvicorn

from talib_altcoins_api.core.config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "talib_altcoins_api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        workers=1 if settings.reload else settings.workers,
        log_config=None,
    )


if __name__ == "__main__":
    main()
