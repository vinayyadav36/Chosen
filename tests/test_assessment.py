"""Tests for scoring engine and report service."""

from __future__ import annotations

from datetime import datetime, timezone

from app.core.scoring_engine import ScoringEngine
from app.models.interview import InterviewDocument
from app.models.schemas import AssessmentReport, Question, ResumeData, TranscriptMessage
from app.services.report_service import ReportService


def _sample_interview() -> InterviewDocument:
    return InterviewDocument(
        _id="test-id",
        candidate_name="Sam",
        jd="python fastapi mongodb docker sql",
        resume_data=ResumeData(
            skills=["python", "fastapi", "docker"],
            experience_years=4,
            education=[],
            projects=["Built API"],
            certifications=[],
        ),
        questions=[
            Question(
                text="Explain async in FastAPI",
                expected_points=["event loop", "await", "I/O"],
                difficulty="medium",
                category="technical",
            )
        ],
        transcript=[
            TranscriptMessage(role="candidate", text="My approach considers edge cases and testing trade-offs.", timestamp=datetime.now(timezone.utc))
        ],
        status="completed",
        created_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )


def test_scoring_engine_calculations() -> None:
    interview = _sample_interview()
    scores = ScoringEngine().calculate_all_scores(interview)
    assert 0 <= scores.overall <= 100


def test_recommendation_logic() -> None:
    engine = ScoringEngine()
    assert engine.get_recommendation(85) == "HIRE"
    assert engine.get_recommendation(65) == "BACKUP"
    assert engine.get_recommendation(40) == "NO_HIRE"


def test_report_generation(tmp_path) -> None:
    report = AssessmentReport(
        interview_id="test-id",
        candidate_name="Sam",
        overall_score=75,
        technical_score=80,
        communication_score=70,
        problem_solving_score=72,
        skills_match_percentage=66,
        recommendation="BACKUP",
        strengths=["technical"],
        weaknesses=["communication"],
        transcript=[],
        pdf_url="",
    )
    filepath = tmp_path / "report.pdf"
    output = ReportService().generate_pdf(report, str(filepath))
    assert filepath.exists()
    assert output.endswith("report.pdf")
