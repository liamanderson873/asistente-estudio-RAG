# Asistente de estudio Implementation Plan

> **For Codex:** Usar la skill executing-plans para implementar y verificar este plan por tareas.

**Goal:** Entregar una primera versión local verificable del asistente RAG.

**Architecture:** API FastAPI e interfaz estática; extracción PDF por página y repositorio PostgreSQL. Ollama encapsulado por un adaptador HTTP, con recuperación léxica/vectorial/híbrida separada de generación.

**Tech Stack:** Python 3.13, FastAPI, psycopg, pgvector, pypdf, httpx, Ollama, pytest, Docker Compose.

---

## Task 1: Ingesta y persistencia

Crear `src/study_rag/{config,domain,pdf,repository}.py`, `sql/001_initial.sql`, `tests/test_pdf.py`, `tests/test_integration.py`. Validar PDF real generado, páginas físicas, fragmentos acotados, restricciones SQL, carga repetida y rollback. Ejecutar `uv run pytest tests/test_pdf.py -q`; esperado: PASS. Integración: `uv run pytest -m integration -q` con `TEST_DATABASE_URL` apuntando exclusivamente a una base de pruebas.

## Task 2: Recuperación y respuestas

Crear `src/study_rag/{ollama,service}.py` y `tests/test_service.py`. Probar RRF con resultados solapados, citas inválidas, abstención y errores HTTP con dobles controlados. Ejecutar `uv run pytest tests/test_service.py -q`; esperado: PASS. Mantener la advertencia de que las citas válidas no prueban fidelidad semántica.

## Task 3: Interfaz y ejecución

Crear `src/study_rag/app.py`, `static/{index.html,app.js,style.css}`, `compose.yaml`, `Dockerfile`, `.env.example`. Probar rutas con FastAPI TestClient sin fingir servicios disponibles. Compose debe enlazar solo localhost y utilizar un volumen independiente del dashboard. Validar con `docker compose config --quiet`.

## Task 4: Corpus y evaluación

Crear `scripts/generate_demo.py`, dos PDFs originales sobre SQL/Python y `evaluation/questions.json`. Crear evaluación léxica/vectorial/híbrida con recall@k y MRR sobre páginas esperadas; no presentar métricas inventadas. Reservar un conjunto de preguntas para comprobación final y no usarlo en ajustes.

## Task 5: Entrega y mapas

Crear README con comandos, limitaciones y verificaciones reales. Ejecutar `uv run ruff check .` y `uv run pytest -q`; tests dependientes de servicios se omiten explícitamente si no están disponibles. Revisar el repositorio con Graphify y Understand Anything, excluyendo dependencias, PDFs y artefactos generados. Registrar el estado real y preparar commit local sin publicar nada.
