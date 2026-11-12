from unittest.mock import Mock

import httpx
import pytest

from study_rag.config import Settings
from study_rag.domain import BackendUnavailable, Hit, InvalidDocument
from study_rag.ollama import OllamaModel
from study_rag.repository import vector_literal
from study_rag.service import StudyService, reciprocal_rank_fusion, validate_answer


def hit(number):
    return Hit(number, "doc", "sql.pdf", 2, "Una clave foránea referencia otra tabla.")


def test_rrf_favors_agreement_and_removes_duplicates():
    result = reciprocal_rank_fusion([[hit(1), hit(2)], [hit(2), hit(3)]], 3)
    assert [h.id for h in result] == [2, 1, 3]
    assert len(reciprocal_rank_fusion([[hit(1), hit(1)]], 5)) == 1


@pytest.mark.parametrize(
    "result",
    [
        {},
        {"sufficient": False},
        {"answer": "SQL", "sufficient": True, "citations": [999]},
        {"answer": "SQL", "sufficient": True, "citations": []},
        {"answer": "SQL", "sufficient": True, "citations": [True]},
        {"answer": "SQL", "sufficient": True, "citations": [1, 999]},
        {"answer": " ", "sufficient": True, "citations": [1]},
        [],
        None,
    ],
)
def test_unusable_model_outputs_abstain(result):
    answer = validate_answer(result, [hit(1)])
    assert answer["abstained"] is True
    assert answer["citations"] == []


def test_citations_are_derived_from_database_not_from_model_metadata():
    answer = validate_answer(
        {"answer": "Referencia otra tabla.", "sufficient": True, "citations": [1, 1]},
        [hit(1)],
    )
    assert answer["abstained"] is False
    assert len(answer["citations"]) == 1
    assert answer["citations"][0]["page"] == 2
    assert answer["citations"][0]["url"].endswith("#page=2")


def test_duplicate_ingestion_does_not_call_embedding_model(pdf_bytes):
    repository, model = Mock(), Mock()
    repository.existing.return_value = "existing-id"
    result = StudyService(repository, model, Settings()).ingest("sql.pdf", pdf_bytes(["SQL"]))
    assert result["duplicate"] is True
    model.embed.assert_not_called()
    repository.store.assert_not_called()


def test_failed_embedding_never_reaches_persistence(pdf_bytes):
    repository, model = Mock(), Mock()
    repository.existing.return_value = None
    model.embed.side_effect = BackendUnavailable("offline")
    with pytest.raises(BackendUnavailable):
        StudyService(repository, model, Settings()).ingest("sql.pdf", pdf_bytes(["SQL"]))
    repository.store.assert_not_called()


def test_ingestion_sanitizes_filename_and_preserves_model(pdf_bytes):
    repository, model = Mock(), Mock()
    repository.existing.return_value = None
    repository.store.return_value = ("id", False)
    model.embed.return_value = [[1.0] * 768]
    service = StudyService(repository, model, Settings())
    service.ingest("../../apuntes.pdf", pdf_bytes(["SQL"]))
    assert repository.store.call_args.args[0] == "apuntes.pdf"
    assert repository.store.call_args.args[-1] == "embeddinggemma"


def test_lexical_search_does_not_require_ollama():
    repository, model = Mock(), Mock()
    repository.search.return_value = [hit(1)]
    service = StudyService(repository, model, Settings())
    assert service.retrieve("clave foránea", "lexical") == [hit(1)]
    model.embed.assert_not_called()


def test_empty_retrieval_does_not_call_generator():
    repository, model = Mock(), Mock()
    repository.search.return_value = []
    assert StudyService(repository, model, Settings()).ask("SQL", "lexical")["abstained"]
    model.answer.assert_not_called()


@pytest.mark.parametrize("vector", [[0.0] * 768, [1.0], [float("nan")] * 768])
def test_rejects_vectors_that_cannot_be_searched(vector):
    with pytest.raises(ValueError):
        vector_literal(vector)


def test_upload_limit_checked_before_parsing():
    service = StudyService(Mock(), Mock(), Settings(max_pdf_bytes=3))
    with pytest.raises(InvalidDocument, match="límite"):
        service.ingest("file.pdf", b"1234")


def test_ollama_connection_failure_becomes_clear_error(monkeypatch):
    def offline(*args, **kwargs):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(httpx, "post", offline)
    with pytest.raises(BackendUnavailable, match="Ollama"):
        OllamaModel(Settings()).embed(["SQL"])


def test_ollama_batches_embeddings_without_silent_truncation(monkeypatch):
    post = Mock(
        return_value=httpx.Response(
            200,
            json={"embeddings": [[1.0] * 768]},
            request=httpx.Request("POST", "http://localhost/api/embed"),
        )
    )
    monkeypatch.setattr(httpx, "post", post)
    assert len(OllamaModel(Settings()).embed(["SQL"])[0]) == 768
    assert post.call_args.kwargs["json"]["truncate"] is False


def test_rejects_missing_embeddings(monkeypatch):
    model = OllamaModel(Settings())
    monkeypatch.setattr(model, "request", lambda *args: {"embeddings": []})
    with pytest.raises(BackendUnavailable):
        model.embed(["SQL"])


@pytest.mark.parametrize("vector", [[1.0], [0.0] * 768, [float("inf")] * 768])
def test_bad_embedding_model_response_becomes_service_error(monkeypatch, vector):
    model = OllamaModel(Settings())
    monkeypatch.setattr(model, "request", lambda *args: {"embeddings": [vector]})
    with pytest.raises(BackendUnavailable, match="768"):
        model.embed(["SQL"])
