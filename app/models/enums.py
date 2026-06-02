"""Enum definitions for interview domain."""

from __future__ import annotations

from enum import Enum


class InterviewMode(str, Enum):
    """Supported interview modes."""

    VOICE = "voice"
    TEXT = "text"


class InterviewStatus(str, Enum):
    """Interview lifecycle statuses."""

    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class RecommendationType(str, Enum):
    """Assessment recommendation options."""

    HIRE = "HIRE"
    BACKUP = "BACKUP"
    NO_HIRE = "NO_HIRE"


class QuestionCategory(str, Enum):
    """Question categories."""

    TECHNICAL = "technical"
    COMMUNICATION = "communication"
    PROBLEM_SOLVING = "problem_solving"
    BEHAVIORAL = "behavioral"
