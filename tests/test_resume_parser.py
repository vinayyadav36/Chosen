import io

from reportlab.pdfgen import canvas

from app.services.resume_service import ResumeService


def _pdf_bytes(text: str) -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(100, 750, text)
    pdf.save()
    return buffer.getvalue()


def test_resume_parser_extracts_core_fields() -> None:
    service = ResumeService()
    parsed = service.parse_pdf_resume(_pdf_bytes('5 years Python FastAPI MongoDB Built project'))
    assert 'python' in parsed.skills
    assert parsed.experience_years >= 5
