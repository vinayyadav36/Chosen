"""Assessment report generation service."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from app.models.schemas import AssessmentReport


class ReportService:
    """Generate JSON and PDF assessment reports."""

    def __init__(self, reports_dir: str = "reports") -> None:
        self._reports_dir = Path(reports_dir)
        self._reports_dir.mkdir(parents=True, exist_ok=True)

    def ensure_reports_directory_exists(self) -> None:
        """Ensure report directory exists."""

        self._reports_dir.mkdir(parents=True, exist_ok=True)

    def generate_json_report(self, report: AssessmentReport) -> dict:
        """Return serializable JSON report payload."""

        return report.model_dump(mode="json")

    def generate_pdf_report(self, report: AssessmentReport) -> str:
        """Generate PDF report and return relative path."""

        self.ensure_reports_directory_exists()
        path = self._reports_dir / f"{report.interview_id}.pdf"
        pdf = canvas.Canvas(str(path), pagesize=LETTER)
        y = 10.5 * inch
        pdf.setFont("Helvetica-Bold", 15)
        pdf.drawString(1 * inch, y, "Hybrid AI Interview Assessment")
        y -= 0.4 * inch

        pdf.setFont("Helvetica", 11)
        rows = [
            f"Interview ID: {report.interview_id}",
            f"Candidate: {report.candidate_name}",
            f"Mode: {report.mode.value}",
            f"Overall Score: {report.score_breakdown.overall_score:.2f}",
            f"Technical: {report.score_breakdown.technical_score:.2f}",
            f"Communication: {report.score_breakdown.communication_score:.2f}",
            f"Problem Solving: {report.score_breakdown.problem_solving_score:.2f}",
            f"Skills Match: {report.skills_match_percentage:.2f}%",
            f"Recommendation: {report.recommendation.value}",
        ]
        for row in rows:
            pdf.drawString(1 * inch, y, row)
            y -= 0.25 * inch

        y -= 0.1 * inch
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(1 * inch, y, "Strengths")
        y -= 0.2 * inch
        pdf.setFont("Helvetica", 10)
        for item in report.strengths:
            pdf.drawString(1.1 * inch, y, f"- {item}")
            y -= 0.18 * inch

        y -= 0.1 * inch
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(1 * inch, y, "Weaknesses")
        y -= 0.2 * inch
        pdf.setFont("Helvetica", 10)
        for item in report.weaknesses:
            pdf.drawString(1.1 * inch, y, f"- {item}")
            y -= 0.18 * inch

        y -= 0.1 * inch
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(1 * inch, y, "Transcript Appendix")
        y -= 0.2 * inch
        pdf.setFont("Helvetica", 9)
        for message in report.transcript[:25]:
            if y < 1.2 * inch:
                pdf.showPage()
                y = 10.5 * inch
                pdf.setFont("Helvetica", 9)
            pdf.drawString(1 * inch, y, f"[{message.role}] {message.text}"[:120])
            y -= 0.17 * inch

        pdf.save()
        return f"/reports/{path.name}"
