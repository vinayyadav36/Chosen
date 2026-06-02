"""Assessment storage document model."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import RecommendationType
from app.models.schemas import ScoreBreakdown


class AssessmentDocument(BaseModel):
    """Stored assessment metadata for an interview."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id")
    interview_id: str
    score_breakdown: ScoreBreakdown
    skills_match_percentage: float
    recommendation: RecommendationType
    strengths: list[str]
    weaknesses: list[str]
    pdf_path: str | None = None
    created_at: datetime
