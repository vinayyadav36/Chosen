"""Resume parsing and feature extraction utilities."""

from __future__ import annotations

import io
import re

import docx
import PyPDF2
import spacy

from app.models.schemas import Education, ResumeData

_SKILL_KEYWORDS = {
    "python",
    "fastapi",
    "django",
    "flask",
    "mongodb",
    "postgresql",
    "aws",
    "docker",
    "kubernetes",
    "langchain",
    "openai",
    "javascript",
    "typescript",
    "react",
    "git",
    "linux",
    "redis",
    "sql",
}

_NLP = spacy.blank("en")


def extract_skills(text: str) -> list[str]:
    """Extract likely technical skills using keyword matching and NLP tokens."""

    lowered = text.lower()
    skills = {skill for skill in _SKILL_KEYWORDS if skill in lowered}
    skills.update(token.text.lower() for token in _NLP(lowered) if token.text.lower() in _SKILL_KEYWORDS)
    return sorted(skills)


def _extract_experience_years(text: str) -> float:
    """Extract years of experience from resume text."""

    matches = re.findall(r"(\d+(?:\.\d+)?)\+?\s+years?", text, flags=re.IGNORECASE)
    return max((float(item) for item in matches), default=0.0)


def _extract_education(text: str) -> list[Education]:
    """Extract simple education entries from resume text."""

    entries: list[Education] = []
    for line in text.splitlines():
        normalized = line.strip()
        if any(word in normalized.lower() for word in ["b.tech", "bachelor", "master", "m.tech", "phd"]):
            entries.append(Education(degree=normalized, institution="Unknown"))
    return entries


def _extract_projects(text: str) -> list[str]:
    """Extract project-like bullet points from text."""

    projects = []
    for line in text.splitlines():
        clean = line.strip("- •\t ")
        if len(clean) > 20 and any(k in clean.lower() for k in ["project", "built", "developed", "implemented"]):
            projects.append(clean)
    return projects[:10]


def _build_resume_data(text: str) -> ResumeData:
    """Build ResumeData object from plain text."""

    return ResumeData(
        skills=extract_skills(text),
        experience_years=_extract_experience_years(text),
        education=_extract_education(text),
        projects=_extract_projects(text),
        certifications=[line.strip() for line in text.splitlines() if "certif" in line.lower()][:5],
    )


def parse_pdf_resume(file: bytes) -> ResumeData:
    """Parse PDF resume bytes and extract structured resume data."""

    reader = PyPDF2.PdfReader(io.BytesIO(file))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    return _build_resume_data(text)


def parse_docx_resume(file: bytes) -> ResumeData:
    """Parse DOCX resume bytes and extract structured resume data."""

    document = docx.Document(io.BytesIO(file))
    text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    return _build_resume_data(text)
