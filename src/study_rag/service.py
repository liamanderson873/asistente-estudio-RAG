import hashlib
from collections import defaultdict
from pathlib import PurePosixPath

from study_rag.config import Settings
from study_rag.domain import Hit, InvalidDocument, Model
from study_rag.pdf import chunk_pages, extract_pages
from study_rag.repository import Repository

ABSTENTION = "No encuentro información suficiente en los documentos para responder con fuentes."


def reciprocal_rank_fusion(rankings: list[list[Hit]], limit: int) -> list[Hit]:
    scores = defaultdict(float)
    hits = {}
    for ranking in rankings:
        seen = set()
        for rank, hit in enumerate(ranking, start=1):
            if hit.id in seen:
                continue
            seen.add(hit.id)
            scores[hit.id] += 1 / (60 + rank)
            hits[hit.id] = hit
    ids = sorted(scores, key=lambda key: (-scores[key], key))[:limit]
    return [hits[key] for key in ids]


def validate_answer(result: dict, hits: list[Hit]) -> dict:
    if not isinstance(result, dict):
        result = {}
    references = result.get("citations")
    allowed = {hit.id: hit for hit in hits}
    valid = (
        result.get("sufficient") is True
        and isinstance(result.get("answer"), str)
        and bool(result["answer"].strip())
        and isinstance(references, list)
        and bool(references)
        and all(type(ref) is int and ref in allowed for ref in references)
    )
    if not valid:
        return {"answer": ABSTENTION, "citations": [], "abstained": True}
    citations = []
    for ref in dict.fromkeys(references):
        hit = allowed[ref]
        citations.append(
            {
                "chunk_id": hit.id,
                "document_id": hit.document_id,
                "document": hit.name,
                "page": hit.page,
                "excerpt": hit.text,
                "url": f"/api/documents/{hit.document_id}/pdf#page={hit.page}",
            }
        )
    return {"answer": result["answer"].strip(), "citations": citations, "abstained": False}


class StudyService:
    def __init__(self, repository: Repository, model: Model, settings: Settings):
        self.repository, self.model, self.settings = repository, model, settings

    def ingest(self, filename: str, data: bytes) -> dict:
        if len(data) > self.settings.max_pdf_bytes:
            raise InvalidDocument("El PDF supera el límite de 10 MB.")
        name = PurePosixPath(filename.replace("\\", "/")).name[:200]
        if not name.lower().endswith(".pdf"):
            raise InvalidDocument("Selecciona un archivo con extensión .pdf.")
        pages = extract_pages(data, self.settings.max_pages)
        digest = hashlib.sha256(data).hexdigest()
        existing = self.repository.existing(digest, self.settings.embedding_model)
        if existing:
            return {"id": existing, "duplicate": True, "pages": len(pages)}
        chunks = chunk_pages(pages)
        vectors = []
        for offset in range(0, len(chunks), 8):
            vectors.extend(self.model.embed([c.text for c in chunks[offset : offset + 8]]))
        doc_id, duplicate = self.repository.store(
            name, data, pages, chunks, vectors, self.settings.embedding_model
        )
        return {"id": doc_id, "duplicate": duplicate, "pages": len(pages)}

    def retrieve(self, question: str, mode: str = "hybrid", limit: int = 5) -> list[Hit]:
        if mode not in {"lexical", "vector", "hybrid"}:
            raise ValueError("Modo de búsqueda desconocido.")
        if not question.strip() or not 1 <= limit <= 10:
            raise ValueError("Introduce una pregunta y un límite entre 1 y 10.")
        candidates = limit * 4
        rankings = []
        if mode in {"lexical", "hybrid"}:
            rankings.append(
                self.repository.search(question, self.settings.embedding_model, candidates)
            )
        if mode in {"vector", "hybrid"}:
            vector = self.model.embed([question])[0]
            rankings.append(
                self.repository.search(question, self.settings.embedding_model, candidates, vector)
            )
        return reciprocal_rank_fusion(rankings, limit)

    def ask(self, question: str, mode: str = "hybrid") -> dict:
        hits = self.retrieve(question, mode, limit=5)[: self.settings.answer_context_chunks]
        if not hits:
            return validate_answer({}, [])
        return validate_answer(self.model.answer(question, hits), hits)
