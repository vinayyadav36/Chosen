"""PDF report generation service."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from app.models.schemas import AssessmentReport


class ReportService:
    """Generates PDF assessment reports."""

    def generate_pdf(self, report: AssessmentReport, filepath: str) -> str:
        """Create PDF report and return written file path."""

        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        pdf = canvas.Canvas(str(path), pagesize=LETTER)
        y = 10.5 * inch
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(1 * inch, y, "AI Interview Assessment Report")

        y -= 0.4 * inch
        pdf.setFont("Helvetica", 11)
        pdf.drawString(1 * inch, y, f"Interview ID: {report.interview_id}")
        y -= 0.25 * inch
        pdf.drawString(1 * inch, y, f"Candidate: {report.candidate_name}")
        y -= 0.25 * inch
        pdf.drawString(1 * inch, y, f"Overall Score: {report.overall_score:.2f}")
        y -= 0.25 * inch
        pdf.drawString(1 * inch, y, f"Technical: {report.technical_score:.2f} | Communication: {report.communication_score:.2f} | Problem Solving: {report.problem_solving_score:.2f}")
        y -= 0.25 * inch
        pdf.drawString(1 * inch, y, f"Recommendation: {report.recommendation}")

        y -= 0.4 * inch
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(1 * inch, y, "Transcript")
        y -= 0.25 * inch
        pdf.setFont("Helvetica", 10)

        for message in report.transcript[:20]:
            text_line = f"[{message.role}] {message.text}"
            if y < 1.2 * inch:
                pdf.showPage()
                y = 10.5 * inch
                pdf.setFont("Helvetica", 10)
            pdf.drawString(1 * inch, y, text_line[:110])
            y -= 0.2 * inch

        pdf.save()
        return str(path)
