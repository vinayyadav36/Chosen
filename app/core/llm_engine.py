"""LLM engine for interview generation and analysis."""

from __future__ import annotations

from statistics import mean

from langchain_openai import ChatOpenAI

from app.models.schemas import CommunicationAnalysis, Evaluation, Question, ResumeData, TranscriptMessage


class LLMEngine:
    """Wraps LLM-powered tasks used by interview workflows."""

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize ChatOpenAI model client."""

        self._api_key = api_key
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.7, api_key=api_key)

    def generate_questions(self, jd: str, resume: ResumeData) -> list[Question]:
        """Generate a balanced set of interview questions."""

        jd_skills = {word.strip(".,") for word in jd.lower().split() if len(word) > 2}
        resume_skills = set(resume.skills)
        skill_gaps = sorted([skill for skill in jd_skills if skill in {"python", "fastapi", "mongodb", "docker", "sql"} and skill not in resume_skills])
        topics = (skill_gaps or sorted(resume_skills) or ["python"])[:5]

        questions: list[Question] = []
        for idx, topic in enumerate(topics, start=1):
            questions.append(
                Question(
                    text=f"Q{idx}. Explain how you would use {topic} in this role.",
                    expected_points=[f"core {topic} concepts", "trade-offs", "real example"],
                    difficulty="medium",
                    category="technical",
                )
            )
        while len(questions) < 8:
            questions.append(
                Question(
                    text=f"Q{len(questions)+1}. Describe a challenging problem you solved and your approach.",
                    expected_points=["problem framing", "solution steps", "result"],
                    difficulty="medium",
                    category="problem_solving" if len(questions) % 2 else "behavioral",
                )
            )
        return questions[:10]

    def evaluate_answer(self, question: Question, answer: str) -> Evaluation:
        """Evaluate answer quality against expected points."""

        answer_lower = answer.lower()
        hits = sum(1 for point in question.expected_points if any(word in answer_lower for word in point.split()))
        score = round(min(10.0, (hits / max(1, len(question.expected_points))) * 10), 2)
        feedback = "Strong answer" if score >= 7 else "Needs more depth and concrete examples"
        return Evaluation(score=score, feedback=feedback)

    def analyze_communication(self, transcript: list[TranscriptMessage]) -> CommunicationAnalysis:
        """Analyze communication quality from transcript text."""

        candidate_messages = [m.text for m in transcript if m.role == "candidate"]
        if not candidate_messages:
            return CommunicationAnalysis(clarity=0, confidence=0, conciseness=0, feedback="No candidate responses captured")

        lengths = [len(message.split()) for message in candidate_messages]
        clarity = min(100.0, round(mean(min(1.0, words / 25) for words in lengths) * 100, 2))
        confidence = min(100.0, round(mean(1.0 if len(msg) > 40 else 0.6 for msg in candidate_messages) * 100, 2))
        conciseness = min(100.0, round(mean(1.0 if words <= 80 else 0.7 for words in lengths) * 100, 2))
        return CommunicationAnalysis(
            clarity=clarity,
            confidence=confidence,
            conciseness=conciseness,
            feedback="Communication is clear and reasonably structured" if clarity >= 60 else "Responses should be clearer and more structured",
        )
