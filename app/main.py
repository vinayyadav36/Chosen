"""FastAPI application entry point."""

from __future__ import annotations

from collections import defaultdict

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo import MongoClient

from app.api.interview import router as interview_router
from app.core.config import settings


class _InMemoryCollection:
    """Simple in-memory collection fallback for local execution and tests."""

    def __init__(self) -> None:
        self.items: dict[str, dict] = {}

    def insert_one(self, payload: dict) -> None:
        self.items[payload["_id"]] = payload

    def find_one(self, query: dict) -> dict | None:
        return self.items.get(query.get("_id"))

    def update_one(self, query: dict, update: dict) -> None:
        item = self.items.get(query.get("_id"))
        if not item:
            return
        if "$set" in update:
            item.update(update["$set"])


class _InMemoryDB(defaultdict):
    """Simple mapping of collections for in-memory fallback."""

    def __init__(self) -> None:
        super().__init__(_InMemoryCollection)


app = FastAPI(title="Voice Interview Platform", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions consistently."""

    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors."""

    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.exception_handler(Exception)
async def unhandled_exception_handler(_, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""

    return JSONResponse(status_code=500, content={"detail": f"Internal server error: {exc}"})


@app.on_event("startup")
async def startup_event() -> None:
    """Connect to MongoDB on startup, fallback to in-memory DB if unavailable."""

    try:
        client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=1500)
        client.admin.command("ping")
        app.state.mongo_client = client
        app.state.db = client[settings.mongodb_db_name]
    except Exception:  # noqa: BLE001
        app.state.mongo_client = None
        app.state.db = _InMemoryDB()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Close MongoDB client on shutdown."""

    client = getattr(app.state, "mongo_client", None)
    if client is not None:
        client.close()


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""

    return {"status": "healthy"}


app.include_router(interview_router)
