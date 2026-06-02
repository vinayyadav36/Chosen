"""Validation helpers for API inputs and provider configuration."""

from __future__ import annotations

from fastapi import HTTPException, UploadFile

from app.models.enums import InterviewMode
from app.utils.constants import ALLOWED_RESUME_MIME_TYPES


def validate_interview_mode(mode: str) -> InterviewMode:
    """Validate and parse interview mode value."""

    try:
        return InterviewMode(mode.lower())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="mode must be either 'voice' or 'text'") from exc


def validate_resume_file_type(file: UploadFile) -> None:
    """Ensure uploaded resume content type is supported."""

    if file.content_type not in ALLOWED_RESUME_MIME_TYPES:
        raise HTTPException(status_code=400, detail="resume must be PDF or DOCX")


def validate_voice_provider_configuration(deepgram_key: str | None, elevenlabs_key: str | None) -> None:
    """Validate required voice provider configuration."""

    if not deepgram_key or not elevenlabs_key:
        raise HTTPException(
            status_code=400,
            detail="voice mode requires DEEPGRAM_API_KEY and ELEVENLABS_API_KEY",
        )
