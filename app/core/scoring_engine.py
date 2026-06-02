"""Scoring engine implementation."""

from __future__ import annotations

from statistics import mean

from app.core.config import settings
from app.models.enums import InterviewMode, RecommendationType
from app.models.schemas import ScoreBreakdown, TranscriptMessage


class ScoringEngine:
    """Calculate category and overall interview scores."""

    def calculate_skills_match(self, jd_skills: list[str], resume_skills: list[str]) -> float:
        """Calculate skills overlap percentage."""

        if not jd_skills:
            return 100.0
        intersection = len(set(jd_skills) & set(resume_skills))
        return round((intersection / len(set(jd_skills))) * 100, 2)

    def calculate_technical_score(self, skills_match: float, eval_scores: list[float]) -> float:
        """Calculate technical score."""

        avg_eval = mean(eval_scores) if eval_scores else 0.0
        return round((skills_match * 0.6) + (avg_eval * 0.4), 2)

    def calculate_communication_score(self, mode: InterviewMode, transcript: list[TranscriptMessage]) -> float:
        """Calculate mode-aware communication score."""

        candidate_msgs = [m.text for m in transcript if m.role == "candidate"]
        if not candidate_msgs:
            return 0.0
        lengths = [len(m.split()) for m in candidate_msgs]
        if mode == InterviewMode.VOICE:
            clarity = min(100.0, mean(min(1.0, l / 18) for l in lengths) * 100)
            structure = min(100.0, mean(1.0 if "." in m or "," in m else 0.7 for m in candidate_msgs) * 100)
            timing = min(100.0, mean(1.0 if l >= 5 else 0.6 for l in lengths) * 100)
            return round((clarity + structure + timing) / 3, 2)
        grammar = min(100.0, mean(1.0 if m[:1].isupper() else 0.7 for m in candidate_msgs) * 100)
        clarity = min(100.0, mean(min(1.0, l / 25) for l in lengths) * 100)
        conciseness = min(100.0, mean(1.0 if l <= 90 else 0.75 for l in lengths) * 100)
        return round((grammar + clarity + conciseness) / 3, 2)

    def calculate_problem_solving_score(self, transcript: list[TranscriptMessage]) -> float:
        """Calculate problem-solving score from reasoning cues."""

        candidate_msgs = [m.text.lower() for m in transcript if m.role == "candidate"]
        if not candidate_msgs:
            return 0.0
        cues = ["trade", "edge", "approach", "assumption", "constraint", "impact", "scale", "test"]
        hit_count = sum(1 for m in candidate_msgs if any(c in m for c in cues))
        return round((hit_count / len(candidate_msgs)) * 100, 2)

    def calculate_overall_score(self, technical: float, communication: float, problem_solving: float) -> float:
        """Calculate weighted overall score."""

        return round((technical * 0.40) + (communication * 0.30) + (problem_solving * 0.30), 2)

    def get_recommendation(self, overall: float) -> RecommendationType:
        """Map overall score to recommendation."""

        if overall >= settings.score_hire_threshold:
            return RecommendationType.HIRE
        if overall >= settings.score_backup_threshold:
            return RecommendationType.BACKUP
        return RecommendationType.NO_HIRE

    def build_score_breakdown(self, technical: float, communication: float, problem_solving: float) -> ScoreBreakdown:
        """Build score breakdown object."""

        overall = self.calculate_overall_score(technical, communication, problem_solving)
        return ScoreBreakdown(
            technical_score=technical,
            communication_score=communication,
            problem_solving_score=problem_solving,
            overall_score=overall,
        )
