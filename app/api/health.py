"""Health route."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health() -> dict[str, object]:
    """Return service health status."""

    return {"status": "healthy", "modes": ["voice", "text"]}
