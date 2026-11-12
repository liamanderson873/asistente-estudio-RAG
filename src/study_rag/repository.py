import hashlib
import math
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row

from study_rag.domain import Chunk, Hit, Page


def vector_literal(vector: list[float]) -> str:
    if len(vector) != 768 or not all(math.isfinite(x) for x in vector):
        raise ValueError("Se requieren embeddings finitos de 768 dimensiones.")
    if not any(vector):
        raise ValueError("El embedding no puede ser un vector nulo.")
    return "[" + ",".join(str(float(x)) for x in vector) + "]"


class Repository:
    def __init__(self, url: str):
        self.url = url

    def connect(self):
        return psycopg.connect(self.url, connect_timeout=3, row_factory=dict_row)

    def existing(self, digest: str, model: str) -> str | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT d.id FROM documents d WHERE sha256=%s AND EXISTS "
                "(SELECT 1 FROM chunks c WHERE c.document_id=d.id AND embedding_model=%s)",
                (digest, model),
            ).fetchone()
            return str(row["id"]) if row else None

    def store(
        self,
        name: str,
        data: bytes,
        pages: list[Page],
        chunks: list[Chunk],
        embeddings: list[list[float]],
        model: str,
    ) -> tuple[str, bool]:
        if len(chunks) != len(embeddings) or not chunks:
            raise ValueError("Debe existir un embedding por fragmento.")
        vectors = [vector_literal(vector) for vector in embeddings]
        digest = hashlib.sha256(data).hexdigest()
        with self.connect() as conn:
            # El bloqueo de transacción serializa dos cargas simultáneas del mismo PDF.
            conn.execute("SELECT pg_advisory_xact_lock(%s)", (int(digest[:15], 16),))
            row = conn.execute("SELECT id FROM documents WHERE sha256=%s", (digest,)).fetchone()
            doc_id = str(row["id"]) if row else str(uuid4())
            if (
                row
                and conn.execute(
                    "SELECT 1 FROM chunks WHERE document_id=%s AND embedding_model=%s LIMIT 1",
                    (doc_id, model),
                ).fetchone()
            ):
                return doc_id, True
            if not row:
                conn.execute(
                    "INSERT INTO documents(id,name,sha256,pdf) VALUES (%s,%s,%s,%s)",
                    (doc_id, name, digest, data),
                )
                with conn.cursor() as cursor:
                    cursor.executemany(
                        "INSERT INTO pages(document_id,number,text) VALUES (%s,%s,%s)",
                        [(doc_id, p.number, p.text) for p in pages],
                    )
            with conn.cursor() as cursor:
                cursor.executemany(
                    "INSERT INTO chunks(document_id,page,ordinal,text,embedding_model,embedding) "
                    "VALUES (%s,%s,%s,%s,%s,%s::vector)",
                    [
                        (doc_id, c.page, c.ordinal, c.text, model, v)
                        for c, v in zip(chunks, vectors, strict=True)
                    ],
                )
        return doc_id, False

    def documents(self) -> list[dict]:
        with self.connect() as conn:
            return conn.execute(
                "SELECT id::text,name,created_at,"
                "(SELECT count(*) FROM pages p WHERE p.document_id=d.id) AS pages "
                "FROM documents d ORDER BY created_at DESC"
            ).fetchall()

    def pdf(self, document_id: str) -> tuple[str, bytes] | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT name,pdf FROM documents WHERE id=%s", (document_id,)
            ).fetchone()
            return (row["name"], bytes(row["pdf"])) if row else None

    def search(
        self, question: str, model: str, limit: int, vector: list[float] | None = None
    ) -> list[Hit]:
        select = (
            "SELECT c.id,c.document_id::text,d.name,c.page,c.text "
            "FROM chunks c JOIN documents d ON d.id=c.document_id "
        )
        if vector is None:
            sql = select + (
                "WHERE c.embedding_model=%s "
                "AND search_vector @@ plainto_tsquery('spanish',%s) "
                "ORDER BY ts_rank_cd(search_vector,plainto_tsquery('spanish',%s)) DESC, c.id "
                "LIMIT %s"
            )
            params = (model, question, question, limit)
        else:
            sql = select + (
                "WHERE c.embedding_model=%s ORDER BY embedding <=> %s::vector,c.id LIMIT %s"
            )
            params = (model, vector_literal(vector), limit)
        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [Hit(**row) for row in rows]
