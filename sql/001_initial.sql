CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS documents (
    id uuid PRIMARY KEY,
    name text NOT NULL,
    sha256 text NOT NULL UNIQUE,
    pdf bytea NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS pages (
    document_id uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    number integer NOT NULL CHECK (number > 0),
    text text NOT NULL,
    PRIMARY KEY (document_id, number)
);
CREATE TABLE IF NOT EXISTS chunks (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_id uuid NOT NULL,
    page integer NOT NULL,
    ordinal integer NOT NULL,
    text text NOT NULL,
    search_vector tsvector GENERATED ALWAYS AS (to_tsvector('spanish', text)) STORED,
    embedding_model text NOT NULL,
    embedding vector(768) NOT NULL,
    FOREIGN KEY (document_id, page) REFERENCES pages(document_id, number) ON DELETE CASCADE,
    UNIQUE (document_id, page, ordinal, embedding_model)
);
CREATE INDEX IF NOT EXISTS chunks_search_idx ON chunks USING gin(search_vector);
CREATE INDEX IF NOT EXISTS chunks_document_idx ON chunks(document_id);
-- Búsqueda vectorial exacta en el corpus pequeño. Medir antes de añadir HNSW.
