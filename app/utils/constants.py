"""Shared constants for interview platform."""

from __future__ import annotations

ALLOWED_RESUME_MIME_TYPES: set[str] = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

ROLE_INTERVIEWER = "interviewer"
ROLE_CANDIDATE = "candidate"

DEFAULT_HIRE_THRESHOLD = 80.0
DEFAULT_BACKUP_THRESHOLD = 60.0

VOICE_EVENT_TRANSCRIPT = "transcript"
VOICE_EVENT_QUESTION = "question"
VOICE_EVENT_AUDIO = "audio"
VOICE_EVENT_STATUS = "status"
VOICE_EVENT_COMPLETED = "completed"
