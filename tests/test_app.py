from unittest.mock import Mock

import psycopg
from fastapi.testclient import TestClient

from study_rag.app import create_app
from study_rag.domain import InvalidDocument


def test_home_is_spanish_and_health_does_not_claim_dependencies_are_ready():
    with TestClient(create_app(Mock())) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert 'lang="es"' in response.text
        assert client.get("/health").json()["dependencies_checked"] is False


def test_database_failure_is_not_shown_as_an_empty_library():
    service = Mock()
    service.repository.documents.side_effect = psycopg.OperationalError("secret host")
    with TestClient(create_app(service)) as client:
        response = client.get("/api/documents")
        assert response.status_code == 503
        assert "secret host" not in response.text


def test_upload_error_is_readable():
    service = Mock()
    service.ingest.side_effect = InvalidDocument("PDF inválido")
    with TestClient(create_app(service)) as client:
        response = client.post("/api/documents", files={"file": ("x.pdf", b"x")})
        assert response.status_code == 422
        assert response.json()["detail"] == "PDF inválido"


def test_question_validation_rejects_unknown_search_mode_and_blank_question():
    service = Mock()
    with TestClient(create_app(service)) as client:
        for payload in [
            {"question": "SQL", "mode": "unknown"},
            {"question": "   "},
        ]:
            assert client.post("/api/ask", json=payload).status_code == 422
    service.ask.assert_not_called()


def test_pdf_route_returns_original_bytes_and_rejects_invalid_uuid():
    service = Mock()
    service.repository.pdf.return_value = ("sql.pdf", b"%PDF-test")
    with TestClient(create_app(service)) as client:
        assert client.get("/api/documents/not-a-uuid/pdf").status_code == 422
        response = client.get("/api/documents/00000000-0000-0000-0000-000000000001/pdf")
        assert response.content == b"%PDF-test"
        assert response.headers["content-type"] == "application/pdf"
