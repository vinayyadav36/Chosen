import io

from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

from app.main import app


def _pdf_bytes(text: str) -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(100, 750, text)
    pdf.save()
    return buffer.getvalue()


def test_text_interview_flow() -> None:
    with TestClient(app) as client:
        start = client.post(
            '/api/interview/start',
            data={
                'jd': 'Need python fastapi mongodb',
                'candidate_name': 'Alex',
                'mode': 'text',
            },
            files={'resume': ('resume.pdf', _pdf_bytes('Python FastAPI MongoDB 4 years'), 'application/pdf')},
        )
        assert start.status_code == 200
        body = start.json()
        interview_id = body['interview_id']

        first = client.post(
            f'/api/interview/{interview_id}/text-message',
            json={'message': 'I built async services with FastAPI and MongoDB in production.'},
        )
        assert first.status_code == 200
        first_payload = first.json()
        assert 'is_complete' in first_payload
        assert first_payload['total_questions'] >= 8
