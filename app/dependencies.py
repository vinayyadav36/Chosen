"""Dependency providers for app settings, DB, and services."""

from __future__ import annotations

from fastapi import Depends, Request

from app.core.config import Settings, get_settings
from app.services.interview_service import InterviewService
from app.services.jd_service import JDService
from app.services.report_service import ReportService
from app.services.resume_service import ResumeService


def get_app_settings() -> Settings:
    """Provide settings dependency."""

    return get_settings()


def get_database(request: Request):
    """Provide database dependency."""

    return request.app.state.db_manager.db


def get_resume_service() -> ResumeService:
    """Provide resume service."""

    return ResumeService()


def get_jd_service() -> JDService:
    """Provide JD service."""

    return JDService()


def get_interview_service(db=Depends(get_database)) -> InterviewService:
    """Provide interview persistence service."""

    return InterviewService(db)


def get_report_service() -> ReportService:
    """Provide report service."""

    return ReportService()
