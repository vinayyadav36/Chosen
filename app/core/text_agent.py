"""Text interview agent state manager."""

from __future__ import annotations

from app.core.llm_engine import LLMEngine
from app.models.enums import InterviewMode
from app.models.schemas import AnswerEvaluation, Question, ResumeData, TranscriptMessage
from app.services.transcript_service import TranscriptService


class TextInterviewAgent:
    """Drive text-mode question/answer flow."""

    def __init__(self, jd_text: str, resume_data: ResumeData, llm_engine: LLMEngine) -> None:
        self._llm = llm_engine
        self._questions = self._llm.generate_questions(jd_text, resume_data, InterviewMode.TEXT)
        self._index = 0
        self._transcript_service = TranscriptService()

    @property
    def questions(self) -> list[Question]:
        """Return generated question bank."""

        return self._questions

    def current_question(self) -> Question | None:
        """Return current question without advancing."""

        if self._index >= len(self._questions):
            return None
        return self._questions[self._index]

    def process_answer(self, transcript: list[TranscriptMessage], answer: str) -> tuple[AnswerEvaluation, Question | None, bool, int, int]:
        """Evaluate answer and advance flow."""

        question = self.current_question()
        if question is None:
            fallback = AnswerEvaluation(score=0, feedback="Interview already completed.", technical=0, communication=0, problem_solving=0)
            return fallback, None, True, len(self._questions), len(self._questions)

        self._transcript_service.append(transcript, "candidate", answer, {"mode": "text"})
        evaluation = self._llm.evaluate_answer(question, answer, InterviewMode.TEXT)
        follow_up = self._llm.generate_follow_up(question, answer, InterviewMode.TEXT)
        if follow_up is not None:
            self._transcript_service.append(transcript, "interviewer", follow_up.text, {"mode": "text", "follow_up": True})
            return evaluation, follow_up, False, self._index + 1, len(self._questions)

        self._index += 1
        next_question = self.current_question()
        if next_question is not None:
            self._transcript_service.append(transcript, "interviewer", next_question.text, {"mode": "text"})
        return evaluation, next_question, self._index >= len(self._questions), self._index, len(self._questions)
