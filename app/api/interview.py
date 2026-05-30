"""Interview API endpoints including start, stream, and report."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, WebSocket, WebSocketDisconnect

from app.api.assessment import generate_assessment_report
from app.api.resume_parser import parse_docx_resume, parse_pdf_resume
from app.core.llm_engine import LLMEngine
from app.core.scoring_engine import ScoringEngine
from app.models.interview import InterviewDocument
from app.models.schemas import InterviewStartResponse, TranscriptMessage
from app.services.deepgram_service import DeepgramService
from app.services.elevenlabs_service import ElevenLabsService
from app.services.report_service import ReportService
from app.utils.helpers import generate_session_token, generate_uuid, validate_file_type

router = APIRouter(prefix="/api/interview", tags=["interview"])


def _collection(request: Request):
    """Return interviews collection from app state."""

    return request.app.state.db["interviews"]


async def _insert_one(request: Request, payload: dict) -> None:
    """Insert one interview record."""

    await asyncio.to_thread(_collection(request).insert_one, payload)


async def _find_one(request: Request, interview_id: str) -> dict | None:
    """Find one interview record by ID."""

    return await asyncio.to_thread(_collection(request).find_one, {"_id": interview_id})


async def _update_one(request: Request, interview_id: str, update: dict) -> None:
    """Update one interview record."""

    await asyncio.to_thread(_collection(request).update_one, {"_id": interview_id}, update)


@router.post("/start", response_model=InterviewStartResponse)
async def start_interview(
    request: Request,
    jd: str = Form(...),
    candidate_name: str = Form(...),
    resume: UploadFile = File(...),
) -> InterviewStartResponse:
    """Start a new interview by parsing resume and generating questions."""

    if not validate_file_type(resume, ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]):
        raise HTTPException(status_code=400, detail="Unsupported file type. Only PDF and DOCX are accepted.")

    try:
        resume_bytes = await resume.read()
        resume_data = (
            parse_pdf_resume(resume_bytes)
            if resume.content_type == "application/pdf"
            else parse_docx_resume(resume_bytes)
        )
        llm_engine = LLMEngine()
        questions = llm_engine.generate_questions(jd, resume_data)

        interview_id = generate_uuid()
        interview = InterviewDocument(
            _id=interview_id,
            candidate_name=candidate_name,
            jd=jd,
            resume_data=resume_data,
            questions=questions,
            transcript=[],
            status="in_progress",
            created_at=datetime.now(timezone.utc),
            completed_at=None,
        )
        await _insert_one(request, interview.model_dump(by_alias=True, mode="json"))
        return InterviewStartResponse(
            interview_id=interview_id,
            session_token=generate_session_token(),
            questions_count=len(questions),
            estimated_duration=f"{max(10, len(questions) * 3)} minutes",
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Failed to start interview: {exc}") from exc


@router.websocket("/{interview_id}/stream")
async def stream_interview(websocket: WebSocket, interview_id: str) -> None:
    """Handle bidirectional interview streaming via websocket."""

    await websocket.accept()
    request = Request(scope=websocket.scope)
    interview_data = await _find_one(request, interview_id)
    if not interview_data:
        await websocket.close(code=4404)
        return

    interview = InterviewDocument(**interview_data)
    llm_engine = LLMEngine()
    stt_service = DeepgramService()
    tts_service = ElevenLabsService()
    current_index = 0

    try:
        while True:
            if current_index >= len(interview.questions):
                await _update_one(
                    request,
                    interview_id,
                    {"$set": {"status": "completed", "completed_at": datetime.now(timezone.utc).isoformat()}},
                )
                await websocket.send_json({"event": "completed"})
                break

            question = interview.questions[current_index]
            await websocket.send_json({"event": "question", "text": question.text, "index": current_index})
            await websocket.send_bytes(await tts_service.generate_speech(question.text))

            payload = await websocket.receive()
            if payload.get("type") == "websocket.disconnect":
                break

            answer_text = payload.get("text") or ""
            if payload.get("bytes"):
                answer_text = await stt_service.transcribe_audio_chunk(payload["bytes"])

            evaluation = llm_engine.evaluate_answer(question, answer_text)
            candidate_message = TranscriptMessage(
                role="candidate",
                text=answer_text,
                timestamp=datetime.now(timezone.utc),
            )
            interviewer_message = TranscriptMessage(
                role="interviewer",
                text=question.text,
                timestamp=datetime.now(timezone.utc),
            )
            interview.transcript.extend([interviewer_message, candidate_message])
            await _update_one(
                request,
                interview_id,
                {
                    "$set": {
                        "transcript": [item.model_dump(mode="json") for item in interview.transcript],
                        "status": "in_progress",
                    }
                },
            )
            await websocket.send_json(
                {
                    "event": "evaluation",
                    "score": evaluation.score,
                    "feedback": evaluation.feedback,
                }
            )
            current_index += 1
    except WebSocketDisconnect:
        return
    except Exception:  # noqa: BLE001
        await websocket.close(code=1011)


@router.get("/{interview_id}/report")
async def get_report(request: Request, interview_id: str) -> dict:
    """Generate JSON and PDF report for one interview."""

    data = await _find_one(request, interview_id)
    if not data:
        raise HTTPException(status_code=404, detail="Interview not found")

    interview = InterviewDocument(**data)
    scoring_engine = ScoringEngine()
    score_breakdown = scoring_engine.calculate_all_scores(interview)

    report = generate_assessment_report(interview)
    report.overall_score = score_breakdown.overall
    report.technical_score = score_breakdown.technical
    report.communication_score = score_breakdown.communication
    report.problem_solving_score = score_breakdown.problem_solving
    report.recommendation = scoring_engine.get_recommendation(score_breakdown.overall)

    report_service = ReportService()
    pdf_path = report_service.generate_pdf(report, str(Path("reports") / f"{interview_id}.pdf"))
    report.pdf_url = pdf_path

    return report.model_dump(mode="json")
