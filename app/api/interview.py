"""Interview routes for start, text mode, voice stream, and report."""

from __future__ import annotations

import base64
import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect

from app.api.assessment import compute_assessment
from app.core.config import get_settings
from app.core.llm_engine import LLMEngine
from app.core.text_agent import TextInterviewAgent
from app.core.voice_agent import VoiceInterviewAgent
from app.dependencies import get_interview_service, get_jd_service, get_resume_service
from app.models.enums import InterviewMode, InterviewStatus
from app.models.interview import InterviewDocument
from app.models.schemas import InterviewStartResponse, TextMessageRequest, TextMessageResponse
from app.services.deepgram_service import DeepgramService
from app.services.elevenlabs_service import ElevenLabsService
from app.services.interview_service import InterviewService
from app.services.jd_service import JDService
from app.services.report_service import ReportService
from app.services.resume_service import ResumeService
from app.services.transcript_service import TranscriptService
from app.utils.helpers import generate_session_token, generate_uuid, utc_now
from app.utils.validators import validate_interview_mode, validate_resume_file_type, validate_voice_provider_configuration

router = APIRouter(prefix="/api/interview", tags=["interview"])


@router.post("/start", response_model=InterviewStartResponse)
async def start_interview(
    jd: str = Form(...),
    candidate_name: str = Form(...),
    mode: str = Form(...),
    resume: UploadFile = File(...),
    resume_service: ResumeService = Depends(get_resume_service),
    jd_service: JDService = Depends(get_jd_service),
    interview_service: InterviewService = Depends(get_interview_service),
) -> InterviewStartResponse:
    """Create a new interview session."""

    interview_mode = validate_interview_mode(mode)
    validate_resume_file_type(resume)

    settings = get_settings()
    if interview_mode == InterviewMode.VOICE:
        validate_voice_provider_configuration(settings.deepgram_api_key, settings.elevenlabs_api_key)

    resume_data = await resume_service.parse_resume(resume)
    normalized_jd = jd_service.normalize_jd(jd)
    required_skills = jd_service.extract_required_skills(normalized_jd)

    llm = LLMEngine(api_key=settings.openai_api_key, default_question_count=settings.default_question_count)
    question_bank = llm.generate_questions(normalized_jd, resume_data, interview_mode)

    session = InterviewDocument(
        _id=generate_uuid(),
        session_token=generate_session_token(),
        candidate_name=candidate_name,
        mode=interview_mode,
        status=InterviewStatus.CREATED,
        jd_text=normalized_jd,
        resume_data=resume_data,
        jd_required_skills=required_skills,
        questions=question_bank,
        current_question_index=0,
        transcript=[],
        scores={},
        report_path=None,
        created_at=utc_now(),
        completed_at=None,
    )
    await interview_service.create_interview(session)

    return InterviewStartResponse(
        interview_id=session.id,
        session_token=session.session_token,
        mode=session.mode,
        questions_count=len(question_bank),
        estimated_duration=f"{max(10, len(question_bank) * 2)} minutes",
    )


@router.post("/{interview_id}/text-message", response_model=TextMessageResponse)
async def text_message(
    interview_id: str,
    payload: TextMessageRequest,
    interview_service: InterviewService = Depends(get_interview_service),
) -> TextMessageResponse:
    """Process one text answer and return next question/progress."""

    interview = await interview_service.get_interview(interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    if interview.mode != InterviewMode.TEXT:
        raise HTTPException(status_code=400, detail="text-message endpoint supports only text mode")

    llm = LLMEngine(api_key=get_settings().openai_api_key)
    agent = TextInterviewAgent(interview.jd_text, interview.resume_data, llm)
    transcript_service = TranscriptService()

    # replay current state
    agent._questions = interview.questions  # noqa: SLF001
    agent._index = interview.current_question_index  # noqa: SLF001
    transcript = interview.transcript
    if agent.current_question() is not None and (not transcript or transcript[-1].role != "interviewer"):
        transcript_service.append(transcript, "interviewer", agent.current_question().text, {"mode": "text"})

    evaluation, next_question, is_complete, question_number, total_questions = agent.process_answer(transcript, payload.message)

    await interview_service.append_transcript(interview_id, transcript, agent._index)  # noqa: SLF001
    await interview_service.update_interview_status(interview_id, InterviewStatus.COMPLETED if is_complete else InterviewStatus.IN_PROGRESS)

    if is_complete:
        await compute_assessment(interview_service, interview_id, ReportService())

    return TextMessageResponse(
        question=next_question.text if next_question else None,
        question_number=question_number,
        total_questions=total_questions,
        is_complete=is_complete,
        evaluation=evaluation,
    )


@router.get("/{interview_id}/report")
async def get_report(
    interview_id: str,
    interview_service: InterviewService = Depends(get_interview_service),
):
    """Return existing report or compute one."""

    assessment = await interview_service.get_assessment_by_interview(interview_id)
    if assessment:
        return {
            "interview_id": assessment.interview_id,
            "score_breakdown": assessment.score_breakdown.model_dump(),
            "skills_match_percentage": assessment.skills_match_percentage,
            "strengths": assessment.strengths,
            "weaknesses": assessment.weaknesses,
            "recommendation": assessment.recommendation.value,
            "pdf_url": assessment.pdf_path,
        }

    report = await compute_assessment(interview_service, interview_id, ReportService())
    return ReportService().generate_json_report(report)


@router.websocket("/{interview_id}/voice-stream")
async def voice_stream(websocket: WebSocket, interview_id: str) -> None:
    """Handle realtime voice interview over WebSocket."""

    await websocket.accept()
    service = InterviewService(websocket.app.state.db_manager.db)
    interview = await service.get_interview(interview_id)
    if not interview:
        await websocket.send_json({"type": "status", "state": "interview_not_found"})
        await websocket.close(code=4404)
        return
    if interview.mode != InterviewMode.VOICE:
        await websocket.send_json({"type": "status", "state": "invalid_mode"})
        await websocket.close(code=4400)
        return

    settings = get_settings()
    stt = DeepgramService(settings.deepgram_api_key)
    tts = ElevenLabsService(settings.elevenlabs_api_key)

    llm = LLMEngine(api_key=settings.openai_api_key)
    agent = VoiceInterviewAgent(interview.jd_text, interview.resume_data, llm)
    agent._questions = interview.questions  # noqa: SLF001
    agent._index = interview.current_question_index  # noqa: SLF001
    transcript = interview.transcript
    transcript_service = TranscriptService()

    current = agent.current_question()
    if current:
        transcript_service.append(transcript, "interviewer", current.text, {"mode": "voice"})
        audio_bytes = await tts.generate_speech(current.text)
        await websocket.send_json({"type": "question", "text": current.text, "question_number": agent._index + 1, "total_questions": len(agent.questions)})  # noqa: SLF001
        await websocket.send_json({"type": "audio", "encoding": "base64", "data": base64.b64encode(audio_bytes).decode("utf-8")})

    try:
        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                break

            answer_text = ""
            if message.get("bytes"):
                answer_text = await stt.transcribe_audio_chunk(message["bytes"])
            elif message.get("text"):
                try:
                    payload = json.loads(message["text"])
                    if payload.get("type") in {"ping", "start", "stop"}:
                        await websocket.send_json({"type": "status", "state": payload.get("type")})
                        continue
                    answer_text = payload.get("message", "")
                except json.JSONDecodeError:
                    answer_text = message["text"]

            if not answer_text:
                await websocket.send_json({"type": "status", "state": "listening"})
                continue

            await websocket.send_json({"type": "transcript", "role": "candidate", "text": answer_text})
            evaluation, next_question, is_complete, question_number, total_questions = agent.process_transcribed_answer(transcript, answer_text)
            await service.append_transcript(interview_id, transcript, agent._index)  # noqa: SLF001
            await websocket.send_json({"type": "status", "state": "processing", "evaluation": evaluation.model_dump()})

            if is_complete:
                await service.update_interview_status(interview_id, InterviewStatus.COMPLETED)
                await compute_assessment(service, interview_id, ReportService())
                await websocket.send_json({"type": "completed"})
                break

            if next_question:
                speech = await tts.generate_speech(next_question.text)
                await websocket.send_json({"type": "question", "text": next_question.text, "question_number": question_number + 1, "total_questions": total_questions})
                await websocket.send_json({"type": "audio", "encoding": "base64", "data": base64.b64encode(speech).decode("utf-8")})
                await service.update_interview_status(interview_id, InterviewStatus.IN_PROGRESS)
    except WebSocketDisconnect:
        await service.append_transcript(interview_id, transcript, agent._index)  # noqa: SLF001
    finally:
        await websocket.close()
