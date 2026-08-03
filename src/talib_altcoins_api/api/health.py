from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {"docs": "/docs", "health": "/healthz"}


@router.get("/healthz")
@router.get("/readyz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}
