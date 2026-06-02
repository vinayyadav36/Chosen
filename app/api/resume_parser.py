"""Resume parser helper endpoints and reusable parsing functions."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile

from app.dependencies import get_resume_service
from app.models.schemas import ResumeData
from app.services.resume_service import ResumeService
from app.utils.validators import validate_resume_file_type

router = APIRouter(prefix="/api/resume", tags=["resume"])


def parse_pdf_resume(file_bytes: bytes, service: ResumeService | None = None) -> ResumeData:
    """Reusable PDF parsing helper."""

    parser = service or ResumeService()
    return parser.parse_pdf_resume(file_bytes)


def parse_docx_resume(file_bytes: bytes, service: ResumeService | None = None) -> ResumeData:
    """Reusable DOCX parsing helper."""

    parser = service or ResumeService()
    return parser.parse_docx_resume(file_bytes)


@router.post("/parse", response_model=ResumeData)
async def parse_resume_endpoint(
    resume: UploadFile = File(...),
    resume_service: ResumeService = Depends(get_resume_service),
) -> ResumeData:
    """Parse uploaded resume into structured data."""

    validate_resume_file_type(resume)
    return await resume_service.parse_resume(resume)
