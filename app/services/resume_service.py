"""Resume parsing service."""

from __future__ import annotations

import io
import re

import docx
import PyPDF2
import spacy
from fastapi import UploadFile

from app.models.schemas import EducationItem, ResumeData


class ResumeService:
    """Parse PDF/DOCX resume and extract structured data."""

    def __init__(self) -> None:
        self._nlp = spacy.blank("en")
        self._skills = {
            "python", "fastapi", "django", "flask", "mongodb", "postgresql", "sql", "docker", "kubernetes",
            "aws", "gcp", "langchain", "openai", "redis", "javascript", "typescript", "react", "git",
        }

    async def parse_resume(self, upload_file: UploadFile) -> ResumeData:
        """Parse uploaded resume file."""

        content = await upload_file.read()
        if upload_file.content_type == "application/pdf":
            return self.parse_pdf_resume(content)
        return self.parse_docx_resume(content)

    def parse_pdf_resume(self, file_bytes: bytes) -> ResumeData:
        """Parse PDF resume bytes."""

        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return self._build_resume_data(text)

    def parse_docx_resume(self, file_bytes: bytes) -> ResumeData:
        """Parse DOCX resume bytes."""

        document = docx.Document(io.BytesIO(file_bytes))
        text = "\n".join(paragraph.text for paragraph in document.paragraphs)
        return self._build_resume_data(text)

    def extract_skills(self, text: str) -> list[str]:
        """Extract skills from text."""

        lowered = text.lower()
        matches = {skill for skill in self._skills if skill in lowered}
        for token in self._nlp(lowered):
            if token.text in self._skills:
                matches.add(token.text)
        return sorted(matches)

    def extract_experience(self, text: str) -> float:
        """Extract years of experience from text."""

        values = re.findall(r"(\d+(?:\.\d+)?)\+?\s+years?", text, flags=re.IGNORECASE)
        return max((float(value) for value in values), default=0.0)

    def extract_education(self, text: str) -> list[EducationItem]:
        """Extract education entries from text."""

        education: list[EducationItem] = []
        for line in text.splitlines():
            clean = line.strip()
            lowered = clean.lower()
            if any(token in lowered for token in ["bachelor", "master", "b.tech", "m.tech", "phd"]):
                education.append(EducationItem(degree=clean, institution="Unknown"))
        return education

    def extract_projects(self, text: str) -> list[str]:
        """Extract project statements from text."""

        projects = []
        for line in text.splitlines():
            clean = line.strip(" -•\t")
            if len(clean) > 15 and any(k in clean.lower() for k in ["project", "built", "developed", "implemented"]):
                projects.append(clean)
        return projects[:10]

    def _build_resume_data(self, text: str) -> ResumeData:
        """Build structured resume object from raw text."""

        certifications = [line.strip() for line in text.splitlines() if "certif" in line.lower()][:5]
        return ResumeData(
            skills=self.extract_skills(text),
            experience_years=self.extract_experience(text),
            education=self.extract_education(text),
            projects=self.extract_projects(text),
            certifications=certifications,
        )
