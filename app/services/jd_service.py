"""Job description parsing service."""

from __future__ import annotations

import re


class JDService:
    """Extract requirements from JD text."""

    def __init__(self) -> None:
        self._known_skills = {
            "python", "fastapi", "django", "flask", "mongodb", "postgresql", "sql", "docker", "kubernetes",
            "aws", "gcp", "langchain", "openai", "redis", "javascript", "typescript", "react", "git",
        }

    def normalize_jd(self, jd_text: str) -> str:
        """Normalize and compact JD content."""

        return " ".join(jd_text.replace("\n", " ").split())

    def extract_required_skills(self, jd_text: str) -> list[str]:
        """Extract must-have skills."""

        lowered = jd_text.lower()
        return sorted(skill for skill in self._known_skills if skill in lowered)

    def extract_optional_skills(self, jd_text: str) -> list[str]:
        """Extract optional skills after 'nice to have'."""

        lowered = jd_text.lower()
        marker = lowered.find("nice to have")
        if marker == -1:
            return []
        tail = lowered[marker:]
        return sorted(skill for skill in self._known_skills if skill in tail)

    def extract_experience_requirement(self, jd_text: str) -> float:
        """Extract minimum years of experience from JD."""

        values = re.findall(r"(\d+(?:\.\d+)?)\+?\s+years?", jd_text, flags=re.IGNORECASE)
        return float(values[0]) if values else 0.0
