"""Database lifecycle and access helpers."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import Settings


class InMemoryCollection:
    """Simple in-memory collection for local fallback/tests."""

    def __init__(self) -> None:
        self._items: dict[str, dict[str, Any]] = {}

    async def insert_one(self, payload: dict[str, Any]) -> None:
        """Insert one document."""

        self._items[payload["_id"]] = payload

    async def find_one(self, query: dict[str, Any]) -> dict[str, Any] | None:
        """Find one document by _id."""

        return self._items.get(query.get("_id"))

    async def update_one(self, query: dict[str, Any], update: dict[str, Any]) -> None:
        """Update a document."""

        item = self._items.get(query.get("_id"))
        if not item:
            return
        for operator, value in update.items():
            if operator == "$set":
                item.update(value)


class InMemoryDatabase(defaultdict[str, InMemoryCollection]):
    """In-memory database mapped by collection name."""

    def __init__(self) -> None:
        super().__init__(InMemoryCollection)


class DatabaseManager:
    """Mongo connection manager with fallback support."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: AsyncIOMotorClient | None = None
        self._db: AsyncIOMotorDatabase | InMemoryDatabase | None = None

    async def connect(self) -> None:
        """Connect to MongoDB or use in-memory fallback."""

        try:
            self._client = AsyncIOMotorClient(self._settings.mongodb_uri, serverSelectionTimeoutMS=1500)
            await self._client.admin.command("ping")
            self._db = self._client[self._settings.mongodb_db_name]
        except Exception:
            self._client = None
            self._db = InMemoryDatabase()

    async def close(self) -> None:
        """Close MongoDB client if active."""

        if self._client is not None:
            self._client.close()

    @property
    def db(self) -> AsyncIOMotorDatabase | InMemoryDatabase:
        """Return active database instance."""

        if self._db is None:
            raise RuntimeError("Database manager not connected")
        return self._db
