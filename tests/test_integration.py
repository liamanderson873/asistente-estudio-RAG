import hashlib
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from study_rag.domain import Chunk, Page
from study_rag.repository import Repository

pytestmark = pytest.mark.integration


@pytest.fixture
def repository():
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Falta TEST_DATABASE_URL: no se ha probado PostgreSQL real.")
    if not conninfo_to_dict(url).get("dbname", "").endswith("_test"):
        pytest.fail("Usa una base dedicada cuyo nombre termine en _test.")
    schema = "study_test_" + uuid4().hex
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    isolated = make_conninfo(url, options=f"-csearch_path={schema},public")
    repository = Repository(isolated)
    try:
        with repository.connect() as conn:
            conn.execute((Path(__file__).parents[1] / "sql/001_initial.sql").read_text())
        yield repository
    finally:
        with psycopg.connect(url, autocommit=True) as conn:
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


def save(repository, data=b"test-pdf", chunks=None):
    return repository.store(
        "sql.pdf",
        data,
        [Page(1, "clave foránea referencia tabla")],
        chunks or [Chunk(1, 0, "clave foránea referencia tabla")],
        [[1.0] + [0.0] * 767],
        "test-model",
    )


def test_ingestion_is_idempotent_and_search_preserves_sources(repository):
    first, duplicate = save(repository)
    assert not duplicate
    assert save(repository) == (first, True)
    assert len(repository.documents()) == 1
    for vector in [None, [1.0] + [0.0] * 767]:
        hits = repository.search("clave foránea", "test-model", 5, vector)
        assert len(hits) == 1
        assert hits[0].document_id == first
        assert hits[0].page == 1
    assert repository.search("clave", "different-model", 5) == []
    assert repository.pdf(first)[1] == b"test-pdf"


def test_foreign_key_failure_rolls_back_entire_document(repository):
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        save(repository, chunks=[Chunk(99, 0, "invalid page")])
    assert repository.documents() == []


def test_concurrent_duplicate_uploads_commit_only_one_document(repository):
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: save(repository), range(2)))
    assert results[0][0] == results[1][0]
    assert sorted(duplicate for _, duplicate in results) == [False, True]
    assert len(repository.documents()) == 1
    assert repository.existing(hashlib.sha256(b"test-pdf").hexdigest(), "test-model")
