from contextlib import asynccontextmanager
from dataclasses import asdict
from pathlib import Path
from typing import Literal
from uuid import UUID

import psycopg
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from study_rag.config import Settings
from study_rag.diagnostics import check_services
from study_rag.domain import BackendUnavailable, InvalidDocument
from study_rag.ollama import OllamaModel
from study_rag.repository import Repository
from study_rag.service import StudyService

STATIC = Path(__file__).parent / "static"


class Question(BaseModel):
    question: str = Field(min_length=3, max_length=1500, pattern=r"\S")
    mode: Literal["lexical", "vector", "hybrid"] = "hybrid"


def create_app(service: StudyService | None = None) -> FastAPI:
    settings = Settings()

    @asynccontextmanager
    async def lifespan(app):
        app.state.service = service or StudyService(
            Repository(settings.database_url), OllamaModel(settings), settings
        )
        yield

    app = FastAPI(title="Asistente de estudio verificable", lifespan=lifespan)

    @app.exception_handler(InvalidDocument)
    async def invalid_document(request, exc):
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(BackendUnavailable)
    async def backend_unavailable(request, exc):
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    @app.exception_handler(psycopg.Error)
    async def database_unavailable(request, exc):
        return JSONResponse(
            status_code=503,
            content={"detail": "PostgreSQL no está disponible o falta inicializar el esquema."},
        )

    @app.get("/health")
    def health():
        return {"status": "ok", "scope": "api", "dependencies_checked": False}

    @app.get("/api/status")
    def status():
        return check_services(app.state.service.repository, settings)

    @app.get("/api/documents")
    def documents():
        return app.state.service.repository.documents()

    @app.post("/api/documents", status_code=201)
    def upload(file: UploadFile = File(...)):
        data = file.file.read(settings.max_pdf_bytes + 1)
        return app.state.service.ingest(file.filename or "", data)

    @app.get("/api/documents/{document_id}/pdf")
    def document_pdf(document_id: UUID):
        result = app.state.service.repository.pdf(str(document_id))
        if result is None:
            raise HTTPException(404, "Documento no encontrado.")
        return Response(
            result[1],
            media_type="application/pdf",
            headers={
                "Content-Disposition": 'inline; filename="documento.pdf"',
                "X-Content-Type-Options": "nosniff",
            },
        )

    @app.post("/api/search")
    def search(question: Question):
        return [asdict(hit) for hit in app.state.service.retrieve(question.question, question.mode)]

    @app.post("/api/ask")
    def ask(question: Question):
        return app.state.service.ask(question.question, question.mode)

    @app.get("/")
    def index():
        return FileResponse(STATIC / "index.html")

    app.mount("/static", StaticFiles(directory=STATIC), name="static")
    return app


app = create_app()
