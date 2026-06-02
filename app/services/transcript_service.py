"""Transcript helper service."""

from __future__ import annotations

from app.models.schemas import TranscriptMessage
from app.utils.helpers import utc_now


class TranscriptService:
    """Build and append transcript entries."""

    def create_entry(self, role: str, text: str, meta: dict | None = None) -> TranscriptMessage:
        """Create normalized transcript message."""

        return TranscriptMessage(role=role, text=text, timestamp=utc_now(), meta=meta or {})

    def append(self, transcript: list[TranscriptMessage], role: str, text: str, meta: dict | None = None) -> list[TranscriptMessage]:
        """Append a transcript entry and return updated list."""

        transcript.append(self.create_entry(role, text, meta))
        return transcript
