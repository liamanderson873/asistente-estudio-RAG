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
