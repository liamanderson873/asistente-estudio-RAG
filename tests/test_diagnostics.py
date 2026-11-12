from unittest.mock import MagicMock, Mock

import httpx
import psycopg
import pytest

from study_rag.config import Settings
from study_rag.diagnostics import check_database, check_ollama, check_services


@pytest.mark.parametrize(
    "vector,schema,ready", [(True, True, True), (False, True, False), (True, False, False)]
)
def test_database_requires_extension_and_schema(vector, schema, ready):
    repository = MagicMock()
    connection = repository.connect.return_value.__enter__.return_value
    connection.execute.return_value.fetchone.return_value = {"vector": vector, "schema": schema}
    assert check_database(repository)["ready"] is ready


def test_database_error_does_not_leak_connection_details():
    repository = MagicMock()
    repository.connect.side_effect = psycopg.OperationalError("password=secret")
    result = check_database(repository)
    assert result["ready"] is False
    assert "secret" not in str(result)


def test_ollama_accepts_latest_alias_and_reports_only_missing_models(monkeypatch):
    response = httpx.Response(
        200,
        json={"models": [{"name": "embeddinggemma:latest"}]},
        request=httpx.Request("GET", "http://localhost/api/tags"),
    )
    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: response)
    result = check_ollama(Settings())
    assert result["ready"] is False
    assert result["missing_models"] == ["qwen2.5:3b"]


def test_unreachable_ollama_is_reported_separately(monkeypatch):
    def offline(*args, **kwargs):
        raise httpx.ConnectError("offline")

    monkeypatch.setattr(httpx, "get", offline)
    assert check_ollama(Settings())["ready"] is False


def test_overall_status_requires_both_dependencies(monkeypatch):
    import study_rag.diagnostics as diagnostics

    monkeypatch.setattr(diagnostics, "check_database", lambda _: {"ready": True})
    monkeypatch.setattr(diagnostics, "check_ollama", lambda _: {"ready": False})
    assert check_services(Mock(), Settings())["ready"] is False
