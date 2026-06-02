"""Pydantic schemas for requests, responses, and core objects."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import InterviewMode, QuestionCategory, RecommendationType


class EducationItem(BaseModel):
    """Education entry extracted from a resume."""

    degree: str
    institution: str
    year: str | None = None


class ResumeData(BaseModel):
    """Structured resume data."""

    skills: list[str] = Field(default_factory=list)
    experience_years: float = 0.0
    education: list[EducationItem] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)


class Question(BaseModel):
    """Interview question model."""

    id: str
    text: str
    category: QuestionCategory
    difficulty: str = "medium"
    expected_points: list[str] = Field(default_factory=list)


class AnswerEvaluation(BaseModel):
    """Answer evaluation result."""

    score: float
    feedback: str
    technical: float
    communication: float
    problem_solving: float
    needs_follow_up: bool = False


class TranscriptMessage(BaseModel):
    """Transcript turn."""

    role: str
    text: str
    timestamp: datetime
    meta: dict[str, str | int | float | bool] = Field(default_factory=dict)


class InterviewStartResponse(BaseModel):
    """Response payload for interview start."""

    interview_id: str
    session_token: str
    mode: InterviewMode
    questions_count: int
    estimated_duration: str


class TextMessageRequest(BaseModel):
    """Request for text answer submission."""

    message: str


class TextMessageResponse(BaseModel):
    """Response for text answer submission."""

    question: str | None
    question_number: int
    total_questions: int
    is_complete: bool
    evaluation: AnswerEvaluation


class ScoreBreakdown(BaseModel):
    """Score breakdown values."""

    technical_score: float
    communication_score: float
    problem_solving_score: float
    overall_score: float


class AssessmentReport(BaseModel):
    """Final assessment report."""

    interview_id: str
    candidate_name: str
    mode: InterviewMode
    score_breakdown: ScoreBreakdown
    skills_match_percentage: float
    strengths: list[str]
    weaknesses: list[str]
    recommendation: RecommendationType
    transcript: list[TranscriptMessage]
    pdf_url: str


class AssessmentSummary(BaseModel):
    """LLM summary output for strengths and weaknesses."""

    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
