"""Assessment data model helpers."""

from pydantic import BaseModel


class AssessmentSummary(BaseModel):
    """Stored assessment summary values."""

    technical_score: float
    communication_score: float
    problem_solving_score: float
    overall_score: float
    recommendation: str
