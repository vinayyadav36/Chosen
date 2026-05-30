"""Central scoring engine used by report generation."""

from __future__ import annotations

from app.api.assessment import (
    calculate_communication_score,
    calculate_problem_solving_score,
    calculate_technical_score,
)
from app.models.interview import InterviewDocument
from app.models.schemas import JDData, ScoreBreakdown


class ScoringEngine:
    """Calculates overall and category-specific interview scores."""

    WEIGHTS = {
        "technical": 0.4,
        "communication": 0.3,
        "problem_solving": 0.3,
    }

    def calculate_technical_score(self, interview: InterviewDocument) -> float:
        """Calculate technical score for an interview."""

        jd = JDData(text=interview.jd, skills=[skill for skill in ["python", "fastapi", "mongodb", "docker", "sql"] if skill in interview.jd.lower()])
        responses = [message.text for message in interview.transcript if message.role == "candidate"]
        return calculate_technical_score(jd=jd, resume=interview.resume_data, responses=responses)

    def calculate_communication_score(self, interview: InterviewDocument) -> float:
        """Calculate communication score for an interview."""

        responses = [message.text for message in interview.transcript if message.role == "candidate"]
        return calculate_communication_score(responses)

    def calculate_problem_solving_score(self, interview: InterviewDocument) -> float:
        """Calculate problem-solving score for an interview."""

        responses = [message.text for message in interview.transcript if message.role == "candidate"]
        return calculate_problem_solving_score(responses)

    def calculate_all_scores(self, interview: InterviewDocument) -> ScoreBreakdown:
        """Calculate all weighted scores and return a score breakdown."""

        technical = self.calculate_technical_score(interview)
        communication = self.calculate_communication_score(interview)
        problem_solving = self.calculate_problem_solving_score(interview)

        overall = (
            technical * self.WEIGHTS["technical"]
            + communication * self.WEIGHTS["communication"]
            + problem_solving * self.WEIGHTS["problem_solving"]
        )

        return ScoreBreakdown(
            technical=round(technical, 2),
            communication=round(communication, 2),
            problem_solving=round(problem_solving, 2),
            overall=round(overall, 2),
        )

    def get_recommendation(self, overall_score: float) -> str:
        """Return recommendation label from overall score."""

        if overall_score >= 80:
            return "HIRE"
        if overall_score >= 60:
            return "BACKUP"
        return "NO_HIRE"
