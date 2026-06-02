"""Application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.assessment import router as assessment_router
from app.api.health import router as health_router
from app.api.interview import router as interview_router
from app.api.resume_parser import router as resume_router
from app.core.config import settings
from app.db import DatabaseManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup/shutdown lifecycle."""

    app.state.db_manager = DatabaseManager(settings)
    await app.state.db_manager.connect()
    Path("reports").mkdir(parents=True, exist_ok=True)
    yield
    await app.state.db_manager.close()


app = FastAPI(title="Hybrid AI Interview Platform", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    """Return consistent JSON for HTTP exceptions."""

    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Return consistent JSON for validation errors."""

    return JSONResponse(status_code=422, content={"error": "validation_error", "details": exc.errors()})


@app.exception_handler(Exception)
async def generic_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    """Return consistent JSON for unhandled errors."""

    return JSONResponse(status_code=500, content={"error": f"internal_error: {exc}"})


app.include_router(health_router)
app.include_router(interview_router)
app.include_router(assessment_router)
app.include_router(resume_router)

frontend_dir = Path("frontend")
if frontend_dir.exists():
    app.mount("/frontend", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
app.mount("/reports", StaticFiles(directory="reports"), name="reports")


@app.get("/")
async def root() -> dict[str, str]:
    """Simple root endpoint."""

    return {"message": "Hybrid AI Interview Platform running", "frontend": "/frontend/index.html"}
