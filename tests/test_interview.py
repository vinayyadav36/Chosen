"""Tests for interview APIs and parsing/generation flows."""

from __future__ import annotations

import io

from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

from app.api.resume_parser import parse_pdf_resume
from app.core.llm_engine import LLMEngine
from app.main import app
from app.models.schemas import ResumeData


def _sample_pdf_bytes(text: str) -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(100, 750, text)
    pdf.save()
    return buffer.getvalue()


def test_resume_parsing_extracts_skills() -> None:
    data = parse_pdf_resume(_sample_pdf_bytes("5 years Python FastAPI MongoDB experience"))
    assert "python" in data.skills


def test_question_generation() -> None:
    engine = LLMEngine()
    questions = engine.generate_questions("Need python fastapi", ResumeData(skills=["python"], experience_years=3, education=[], projects=[], certifications=[]))
    assert len(questions) >= 8


def test_start_interview_endpoint() -> None:
    with TestClient(app) as client:
        files = {
            "resume": ("resume.pdf", _sample_pdf_bytes("Python FastAPI Docker"), "application/pdf"),
        }
        response = client.post(
            "/api/interview/start",
            data={"jd": "Need python fastapi mongodb", "candidate_name": "Alex"},
            files=files,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["interview_id"]
        assert body["questions_count"] >= 8


def test_websocket_connection() -> None:
    with TestClient(app) as client:
        files = {
            "resume": ("resume.pdf", _sample_pdf_bytes("Python FastAPI Docker"), "application/pdf"),
        }
        start = client.post(
            "/api/interview/start",
            data={"jd": "Need python fastapi mongodb", "candidate_name": "Alex"},
            files=files,
        )
        interview_id = start.json()["interview_id"]

        with client.websocket_connect(f"/api/interview/{interview_id}/stream") as websocket:
            first_question = websocket.receive_json()
            assert first_question["event"] == "question"
            websocket.receive_bytes()
            websocket.send_text("I used FastAPI with async and MongoDB in production")
            evaluation = websocket.receive_json()
            assert evaluation["event"] == "evaluation"
