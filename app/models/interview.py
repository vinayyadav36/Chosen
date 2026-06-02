"""Interview storage document model."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import InterviewMode, InterviewStatus
from app.models.schemas import Question, ResumeData, TranscriptMessage


class InterviewDocument(BaseModel):
    """MongoDB-backed interview session model."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id")
    session_token: str
    candidate_name: str
    mode: InterviewMode
    status: InterviewStatus
    jd_text: str
    resume_data: ResumeData
    jd_required_skills: list[str] = Field(default_factory=list)
    questions: list[Question] = Field(default_factory=list)
    current_question_index: int = 0
    transcript: list[TranscriptMessage] = Field(default_factory=list)
    scores: dict[str, float] = Field(default_factory=dict)
    report_path: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
