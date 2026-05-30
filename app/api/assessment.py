"""Assessment scoring helpers."""

from __future__ import annotations

from app.core.llm_engine import LLMEngine
from app.models.interview import InterviewDocument
from app.models.schemas import AssessmentReport, JDData, ResumeData, TranscriptMessage


def _jaccard_similarity(first: set[str], second: set[str]) -> float:
    """Compute Jaccard similarity for two sets."""

    if not first and not second:
        return 1.0
    union = first | second
    if not union:
        return 0.0
    return len(first & second) / len(union)


def calculate_technical_score(jd: JDData, resume: ResumeData, responses: list[str]) -> float:
    """Calculate technical score from skill overlap and response depth."""

    similarity = _jaccard_similarity(set(jd.skills), set(resume.skills)) * 100
    response_quality = min(100.0, float(sum(len(item.split()) for item in responses))) / max(1, len(responses) * 20) * 100
    return round((similarity * 0.6) + (response_quality * 0.4), 2)


def calculate_communication_score(responses: list[str]) -> float:
    """Calculate communication score from answer clarity signals."""

    if not responses:
        return 0.0
    llm_engine = LLMEngine()
    transcript = [
        TranscriptMessage(role="candidate", text=response, timestamp=__import__("datetime").datetime.now(__import__("datetime").timezone.utc))
        for response in responses
    ]
    analysis = llm_engine.analyze_communication(transcript)
    return round((analysis.clarity + analysis.confidence + analysis.conciseness) / 3, 2)


def calculate_problem_solving_score(responses: list[str]) -> float:
    """Calculate problem-solving score using reasoning indicators."""

    keywords = {"edge", "trade-off", "approach", "assumption", "complexity", "test"}
    if not responses:
        return 0.0
    keyword_hits = sum(1 for response in responses if any(keyword in response.lower() for keyword in keywords))
    return round((keyword_hits / len(responses)) * 100, 2)


def generate_assessment_report(interview: InterviewDocument) -> AssessmentReport:
    """Generate complete assessment report from interview document."""

    jd_tokens = {word.strip(".,").lower() for word in interview.jd.split() if len(word) > 2}
    jd = JDData(text=interview.jd, skills=sorted({skill for skill in jd_tokens if skill in {"python", "fastapi", "mongodb", "docker", "sql"}}))
    responses = [msg.text for msg in interview.transcript if msg.role == "candidate"]

    technical = calculate_technical_score(jd=jd, resume=interview.resume_data, responses=responses)
    communication = calculate_communication_score(responses=responses)
    problem_solving = calculate_problem_solving_score(responses=responses)
    overall = round((technical * 0.4) + (communication * 0.3) + (problem_solving * 0.3), 2)

    recommendation = "HIRE" if overall >= 80 else "BACKUP" if overall >= 60 else "NO_HIRE"
    strengths = ["Technical fundamentals"] if technical >= 60 else []
    if communication >= 60:
        strengths.append("Clear communication")
    weaknesses = [] if problem_solving >= 60 else ["Needs stronger structured problem-solving answers"]

    skills_match = round(_jaccard_similarity(set(jd.skills), set(interview.resume_data.skills)) * 100, 2)
    return AssessmentReport(
        interview_id=interview.id,
        candidate_name=interview.candidate_name,
        overall_score=overall,
        technical_score=technical,
        communication_score=communication,
        problem_solving_score=problem_solving,
        skills_match_percentage=skills_match,
        recommendation=recommendation,
        strengths=strengths,
        weaknesses=weaknesses,
        transcript=interview.transcript,
        pdf_url="",
    )
