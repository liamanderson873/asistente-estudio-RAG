"""Comprobaciones de disponibilidad; no ejecutan inferencia ni alteran datos."""

import httpx
import psycopg

from study_rag.config import Settings
from study_rag.repository import Repository


def check_database(repository: Repository) -> dict:
    try:
        with repository.connect() as conn:
            row = conn.execute(
                "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname='vector') AS vector, "
                "to_regclass('documents') IS NOT NULL AND to_regclass('pages') IS NOT NULL "
                "AND to_regclass('chunks') IS NOT NULL AS schema"
            ).fetchone()
        ready = bool(row["vector"] and row["schema"])
        return {
            "ready": ready,
            "message": "Biblioteca disponible." if ready else "Falta inicializar la biblioteca.",
        }
    except psycopg.Error:
        return {
            "ready": False,
            "message": "Biblioteca sin conexión. Inicia la base de datos local.",
        }


def check_ollama(settings: Settings) -> dict:
    try:
        response = httpx.get(settings.ollama_url + "/api/tags", timeout=5)
        response.raise_for_status()
        data = response.json()
        names = {item["name"] for item in data["models"]}
        expected = [settings.embedding_model, settings.chat_model]
        missing = [name for name in expected if name not in names and name + ":latest" not in names]
        return {
            "ready": not missing,
            "message": "Modelos locales disponibles." if not missing else "Faltan modelos locales.",
            "missing_models": missing,
        }
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        return {
            "ready": False,
            "message": "Motor de IA sin conexión. Inicia Ollama local.",
            "missing_models": [],
        }


def check_services(repository: Repository, settings: Settings) -> dict:
    database = check_database(repository)
    ollama = check_ollama(settings)
    return {
        "ready": database["ready"] and ollama["ready"],
        "database": database,
        "ollama": ollama,
        "scope": "availability_only",
    }
