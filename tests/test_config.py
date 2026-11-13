import pytest
from pydantic import ValidationError

from study_rag.config import Settings


def test_embedding_dimensions_can_be_loaded_from_environment(monkeypatch):
    monkeypatch.setenv("EMBEDDING_DIMENSIONS", "768")
    assert Settings(_env_file=None).embedding_dimensions == 768


@pytest.mark.parametrize("value", ["384", "1024", "invalid"])
def test_incompatible_embedding_dimensions_are_rejected(monkeypatch, value):
    monkeypatch.setenv("EMBEDDING_DIMENSIONS", value)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


@pytest.mark.parametrize("value", [0, 6])
def test_context_budget_rejects_empty_or_excessive_context(value):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, answer_context_chunks=value)
