"""LLM-driven question and answer orchestration."""

from __future__ import annotations

from statistics import mean

from langchain_openai import ChatOpenAI

from app.models.enums import InterviewMode, QuestionCategory
from app.models.schemas import AnswerEvaluation, AssessmentSummary, Question, ResumeData, TranscriptMessage
from app.utils.helpers import generate_uuid


class LLMEngine:
    """Generate questions and evaluate candidate answers."""

    def __init__(self, api_key: str | None = None, default_question_count: int = 8) -> None:
        self._api_key = api_key
        self._default_question_count = max(8, min(default_question_count, 10))
        self._model = ChatOpenAI(model="gpt-4o-mini", api_key=api_key, temperature=0.2) if api_key else None

    def generate_questions(self, jd_text: str, resume_data: ResumeData, mode: InterviewMode) -> list[Question]:
        """Generate an interview question bank from JD and resume."""

        jd_skills = {token.strip(".,").lower() for token in jd_text.split() if len(token) > 2}
        gaps = sorted(skill for skill in jd_skills if skill in {"python", "fastapi", "mongodb", "docker", "sql", "redis"} and skill not in set(resume_data.skills))
        targets = gaps or resume_data.skills or ["problem-solving"]

        questions: list[Question] = []
        for topic in targets[:5]:
            prefix = "Could you briefly explain" if mode == InterviewMode.VOICE else "Explain in detail"
            questions.append(
                Question(
                    id=generate_uuid(),
                    text=f"{prefix} your practical experience with {topic}?",
                    category=QuestionCategory.TECHNICAL,
                    expected_points=["context", "implementation", "trade-offs"],
                )
            )

        while len(questions) < self._default_question_count:
            idx = len(questions)
            category = QuestionCategory.PROBLEM_SOLVING if idx % 2 == 0 else QuestionCategory.COMMUNICATION
            prompt = (
                "Walk me through a challenging production issue and how you resolved it."
                if mode == InterviewMode.VOICE
                else "Describe a complex production problem you solved, including constraints, alternatives, and measurable results."
            )
            questions.append(
                Question(
                    id=generate_uuid(),
                    text=prompt,
                    category=category,
                    expected_points=["structure", "reasoning", "outcome"],
                )
            )
        return questions[:10]

    def evaluate_answer(self, question: Question, answer: str, mode: InterviewMode) -> AnswerEvaluation:
        """Evaluate candidate answer quality."""

        lowered = answer.lower()
        hits = sum(1 for p in question.expected_points if any(w in lowered for w in p.split()))
        length_factor = min(1.0, len(answer.split()) / (35 if mode == InterviewMode.TEXT else 20))
        technical = round(min(100.0, (hits / max(1, len(question.expected_points))) * 100), 2)
        communication = round(min(100.0, 55 + (45 * length_factor)), 2)
        problem_solving = round(min(100.0, technical * 0.6 + communication * 0.4), 2)
        score = round((technical * 0.4 + communication * 0.3 + problem_solving * 0.3) / 10, 2)
        needs_follow_up = score < 6.0
        feedback = "Good answer with clear structure." if score >= 7 else "Needs more depth and concrete examples."
        return AnswerEvaluation(
            score=score,
            feedback=feedback,
            technical=technical,
            communication=communication,
            problem_solving=problem_solving,
            needs_follow_up=needs_follow_up,
        )

    def generate_follow_up(self, question: Question, answer: str, mode: InterviewMode) -> Question | None:
        """Generate a follow-up question when evaluation indicates gaps."""

        evaluation = self.evaluate_answer(question, answer, mode)
        if not evaluation.needs_follow_up:
            return None
        text = "Can you give one concrete production example and decision trade-off?" if mode == InterviewMode.VOICE else "Please provide a specific production example, design trade-off, and measurable impact for your answer."
        return Question(
            id=generate_uuid(),
            text=text,
            category=question.category,
            expected_points=["example", "trade-off", "impact"],
            difficulty="medium",
        )

    def summarize_strengths_weaknesses(self, transcript: list[TranscriptMessage], scores: dict[str, float]) -> AssessmentSummary:
        """Create concise strengths and weaknesses summary."""

        candidate_messages = [m.text for m in transcript if m.role == "candidate"]
        avg_words = mean([len(msg.split()) for msg in candidate_messages]) if candidate_messages else 0

        strengths: list[str] = []
        weaknesses: list[str] = []

        if scores.get("technical_score", 0) >= 70:
            strengths.append("Strong technical grounding aligned to job requirements")
        if scores.get("problem_solving_score", 0) >= 70:
            strengths.append("Good problem-solving structure and trade-off thinking")
        if avg_words >= 25:
            strengths.append("Provides complete and reasonably detailed answers")

        if scores.get("communication_score", 0) < 60:
            weaknesses.append("Communication clarity and structure need improvement")
        if scores.get("technical_score", 0) < 60:
            weaknesses.append("Needs deeper technical examples and implementation detail")
        if avg_words < 12:
            weaknesses.append("Answers are often too brief and lack concrete context")

        if not strengths:
            strengths.append("Consistent participation across interview rounds")
        if not weaknesses:
            weaknesses.append("No major weaknesses identified from current transcript")

        return AssessmentSummary(strengths=strengths[:3], weaknesses=weaknesses[:3])
