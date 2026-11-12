import re
from io import BytesIO

from pypdf import PdfReader

from study_rag.domain import Chunk, InvalidDocument, Page


def extract_pages(data: bytes, max_pages: int = 100) -> list[Page]:
    if not data.startswith(b"%PDF-"):
        raise InvalidDocument("El archivo no es un PDF válido.")
    try:
        reader = PdfReader(BytesIO(data))
        if reader.is_encrypted:
            raise InvalidDocument("Esta versión no admite PDFs cifrados.")
        if not 1 <= len(reader.pages) <= max_pages:
            raise InvalidDocument(f"El PDF debe tener entre 1 y {max_pages} páginas.")
        pages = [
            Page(i, re.sub(r"\s+", " ", page.extract_text() or "").strip())
            for i, page in enumerate(reader.pages, start=1)
        ]
    except InvalidDocument:
        raise
    except Exception as exc:
        raise InvalidDocument("No se ha podido leer el PDF.") from exc
    if not any(page.text for page in pages):
        raise InvalidDocument("El PDF no contiene texto extraíble; OCR no está disponible.")
    return pages


def chunk_pages(pages: list[Page], size: int = 140, overlap: int = 25) -> list[Chunk]:
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError("El solapamiento debe ser menor que el tamaño del fragmento.")
    chunks = []
    for page in pages:
        words = page.text.split()
        start, ordinal = 0, 0
        while start < len(words):
            chunks.append(Chunk(page.number, ordinal, " ".join(words[start : start + size])))
            if start + size >= len(words):
                break
            start += size - overlap
            ordinal += 1
    return chunks
