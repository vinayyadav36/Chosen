"""General utility helper functions."""

from __future__ import annotations

import secrets
import uuid

from fastapi import UploadFile


def generate_uuid() -> str:
    """Generate a random UUID string."""

    return str(uuid.uuid4())


def generate_session_token() -> str:
    """Generate a secure session token for interviews."""

    return secrets.token_urlsafe(32)


def validate_file_type(file: UploadFile, allowed_types: list[str]) -> bool:
    """Validate uploaded file content type against allowed values."""

    return file.content_type in allowed_types
