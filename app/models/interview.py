"""Interview document model for MongoDB storage."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.schemas import Question, ResumeData, TranscriptMessage


class InterviewDocument(BaseModel):
    """Represents a stored interview record."""

    id: str = Field(alias="_id")
    candidate_name: str
    jd: str
    resume_data: ResumeData
    questions: list[Question]
    transcript: list[TranscriptMessage] = Field(default_factory=list)
    status: str
    created_at: datetime
    completed_at: datetime | None = None
