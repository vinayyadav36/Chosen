"""Assessment-related endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.core.llm_engine import LLMEngine
from app.core.scoring_engine import ScoringEngine
from app.dependencies import get_interview_service
from app.models.assessment import AssessmentDocument
from app.models.schemas import AssessmentReport
from app.services.interview_service import InterviewService
from app.services.report_service import ReportService
from app.utils.helpers import generate_uuid, utc_now

router = APIRouter(prefix="/api/assessment", tags=["assessment"])


async def compute_assessment(interview_service: InterviewService, interview_id: str, report_service: ReportService) -> AssessmentReport:
    """Compute and persist assessment report for interview."""

    interview = await interview_service.get_interview(interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    scorer = ScoringEngine()
    eval_scores = [
        min(100.0, max(0.0, len(msg.text.split()) * 3.0))
        for msg in interview.transcript
        if msg.role == "candidate"
    ]
    skills_match = scorer.calculate_skills_match(interview.jd_required_skills, interview.resume_data.skills)
    technical = scorer.calculate_technical_score(skills_match, eval_scores)
    communication = scorer.calculate_communication_score(interview.mode, interview.transcript)
    problem_solving = scorer.calculate_problem_solving_score(interview.transcript)
    breakdown = scorer.build_score_breakdown(technical, communication, problem_solving)
    recommendation = scorer.get_recommendation(breakdown.overall_score)

    summary = LLMEngine().summarize_strengths_weaknesses(interview.transcript, breakdown.model_dump())

    report = AssessmentReport(
        interview_id=interview.id,
        candidate_name=interview.candidate_name,
        mode=interview.mode,
        score_breakdown=breakdown,
        skills_match_percentage=skills_match,
        strengths=summary.strengths,
        weaknesses=summary.weaknesses,
        recommendation=recommendation,
        transcript=interview.transcript,
        pdf_url="",
    )

    pdf_url = report_service.generate_pdf_report(report)
    report.pdf_url = pdf_url

    assessment_doc = AssessmentDocument(
        _id=generate_uuid(),
        interview_id=interview.id,
        score_breakdown=breakdown,
        skills_match_percentage=skills_match,
        recommendation=recommendation,
        strengths=summary.strengths,
        weaknesses=summary.weaknesses,
        pdf_path=pdf_url,
        created_at=utc_now(),
    )
    await interview_service.store_scores(interview.id, breakdown.model_dump())
    await interview_service.store_assessment(assessment_doc)
    await interview_service.finalize_interview(interview.id, pdf_url)

    return report


@router.post("/{interview_id}/recompute", response_model=AssessmentReport)
async def recompute_assessment(
    interview_id: str,
    interview_service: InterviewService = Depends(get_interview_service),
) -> AssessmentReport:
    """Recompute assessment for one interview."""

    return await compute_assessment(interview_service, interview_id, ReportService())
