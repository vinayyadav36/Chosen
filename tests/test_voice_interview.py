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


def test_voice_websocket_route() -> None:
    with TestClient(app) as client:
        start = client.post(
            '/api/interview/start',
            data={
                'jd': 'Need python fastapi mongodb',
                'candidate_name': 'Voice User',
                'mode': 'voice',
            },
            files={'resume': ('resume.pdf', _pdf_bytes('Python FastAPI MongoDB'), 'application/pdf')},
        )
        # missing keys allowed in tests only when route rejects cleanly
        if start.status_code == 400:
            assert 'voice mode requires' in start.json()['error']
            return

        interview_id = start.json()['interview_id']
        with client.websocket_connect(f'/api/interview/{interview_id}/voice-stream') as ws:
            first = ws.receive_json()
            assert first['type'] == 'question'
            ws.send_text('I used FastAPI and MongoDB in distributed systems')
            status = ws.receive_json()
            assert status['type'] in {'transcript', 'status'}
