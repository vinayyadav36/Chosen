"""Interview flow controller for voice and text sessions."""

from __future__ import annotations

from datetime import datetime, timezone

from app.core.llm_engine import LLMEngine
from app.models.schemas import Evaluation, Question, ResumeData, TranscriptMessage


class VoiceInterviewAgent:
    """Stateful interview agent handling question flow and evaluations."""

    def __init__(self, jd: str, resume: ResumeData) -> None:
        """Initialize interview agent with generated questions."""

        self.jd = jd
        self.resume = resume
        self.llm_engine = LLMEngine()
        self.questions = self.llm_engine.generate_questions(jd, resume)
        self.transcript: list[TranscriptMessage] = []
        self.current_question_idx = 0

    async def get_next_question(self) -> Question | None:
        """Return next question and advance internal pointer."""

        if self.current_question_idx >= len(self.questions):
            return None
        question = self.questions[self.current_question_idx]
        self.current_question_idx += 1
        self.transcript.append(
            TranscriptMessage(role="interviewer", text=question.text, timestamp=datetime.now(timezone.utc))
        )
        return question

    async def process_answer(self, answer: str) -> Evaluation:
        """Evaluate current answer and add to transcript."""

        question_index = max(0, self.current_question_idx - 1)
        evaluation = self.llm_engine.evaluate_answer(self.questions[question_index], answer)
        self.transcript.append(
            TranscriptMessage(role="candidate", text=answer, timestamp=datetime.now(timezone.utc))
        )
        return evaluation

    async def generate_follow_up(self, question: Question, answer: str) -> Question:
        """Generate follow-up question based on answer quality."""

        evaluation = self.llm_engine.evaluate_answer(question, answer)
        prompt = "deeper technical details" if evaluation.score < 6 else "scalability and trade-offs"
        return Question(
            text=f"Follow-up: Can you elaborate on {prompt} related to your previous answer?",
            expected_points=["context", "decision making", "impact"],
            difficulty="medium",
            category=question.category,
        )

    def get_completion_status(self) -> dict[str, int | bool]:
        """Return current interview completion status."""

        return {
            "questions_asked": self.current_question_idx,
            "questions_total": len(self.questions),
            "is_complete": self.current_question_idx >= len(self.questions),
        }
