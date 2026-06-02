from app.core.scoring_engine import ScoringEngine
from app.models.enums import InterviewMode, RecommendationType
from app.models.schemas import AssessmentReport, TranscriptMessage
from app.services.report_service import ReportService
from app.utils.helpers import utc_now


def test_recommendation_thresholds() -> None:
    engine = ScoringEngine()
    assert engine.get_recommendation(85) == RecommendationType.HIRE
    assert engine.get_recommendation(65) == RecommendationType.BACKUP
    assert engine.get_recommendation(45) == RecommendationType.NO_HIRE


def test_report_json_structure() -> None:
    engine = ScoringEngine()
    breakdown = engine.build_score_breakdown(80, 70, 75)
    transcript = [TranscriptMessage(role='candidate', text='I used fastapi and mongodb.', timestamp=utc_now(), meta={})]
    report = AssessmentReport(
        interview_id='id-1',
        candidate_name='Sam',
        mode=InterviewMode.TEXT,
        score_breakdown=breakdown,
        skills_match_percentage=76.0,
        strengths=['good architecture'],
        weaknesses=['limited scale examples'],
        recommendation=engine.get_recommendation(breakdown.overall_score),
        transcript=transcript,
        pdf_url='/reports/id-1.pdf',
    )
    report_json = ReportService().generate_json_report(report)
    assert report_json['interview_id'] == 'id-1'
    assert report_json['recommendation'] in {'HIRE', 'BACKUP', 'NO_HIRE'}
