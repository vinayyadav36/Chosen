"""Interview persistence service."""

from __future__ import annotations

from typing import Any

from app.models.assessment import AssessmentDocument
from app.models.enums import InterviewStatus
from app.models.interview import InterviewDocument
from app.models.schemas import Question, TranscriptMessage
from app.utils.helpers import utc_now


class InterviewService:
    """CRUD operations for interview sessions and assessments."""

    def __init__(self, db: Any) -> None:
        self._db = db

    @property
    def interviews(self):
        """Interviews collection accessor."""

        return self._db["interviews"]

    @property
    def assessments(self):
        """Assessments collection accessor."""

        return self._db["assessments"]

    async def create_interview(self, interview: InterviewDocument) -> None:
        """Create a new interview record."""

        await self.interviews.insert_one(interview.model_dump(by_alias=True, mode="json"))

    async def get_interview(self, interview_id: str) -> InterviewDocument | None:
        """Fetch interview by ID."""

        data = await self.interviews.find_one({"_id": interview_id})
        return InterviewDocument(**data) if data else None

    async def update_interview_status(self, interview_id: str, status: InterviewStatus) -> None:
        """Update interview status."""

        await self.interviews.update_one({"_id": interview_id}, {"$set": {"status": status.value}})

    async def store_questions(self, interview_id: str, questions: list[Question]) -> None:
        """Store generated interview questions."""

        await self.interviews.update_one(
            {"_id": interview_id},
            {"$set": {"questions": [q.model_dump(mode="json") for q in questions]}},
        )

    async def append_transcript(self, interview_id: str, transcript: list[TranscriptMessage], current_index: int) -> None:
        """Persist transcript and current question index."""

        await self.interviews.update_one(
            {"_id": interview_id},
            {
                "$set": {
                    "transcript": [entry.model_dump(mode="json") for entry in transcript],
                    "current_question_index": current_index,
                }
            },
        )

    async def store_scores(self, interview_id: str, scores: dict[str, float]) -> None:
        """Store computed scores."""

        await self.interviews.update_one({"_id": interview_id}, {"$set": {"scores": scores}})

    async def finalize_interview(self, interview_id: str, report_path: str) -> None:
        """Mark interview completed."""

        await self.interviews.update_one(
            {"_id": interview_id},
            {
                "$set": {
                    "status": InterviewStatus.COMPLETED.value,
                    "completed_at": utc_now().isoformat(),
                    "report_path": report_path,
                }
            },
        )

    async def store_assessment(self, assessment: AssessmentDocument) -> None:
        """Store assessment document."""

        await self.assessments.insert_one(assessment.model_dump(by_alias=True, mode="json"))

    async def get_assessment_by_interview(self, interview_id: str) -> AssessmentDocument | None:
        """Retrieve assessment by interview id."""

        data = await self.assessments.find_one({"interview_id": interview_id})
        return AssessmentDocument(**data) if data else None
