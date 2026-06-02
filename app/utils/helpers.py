"""General helper utilities."""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timezone


def generate_uuid() -> str:
    """Generate a UUID string."""

    return str(uuid.uuid4())


def generate_session_token() -> str:
    """Generate an interview session token."""

    return secrets.token_urlsafe(32)


def utc_now() -> datetime:
    """Return timezone aware UTC datetime."""

    return datetime.now(timezone.utc)


def iso_utc_now() -> str:
    """Return ISO-8601 UTC timestamp."""

    return utc_now().isoformat()
