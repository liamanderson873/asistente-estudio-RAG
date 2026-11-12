import pytest
from pypdf import PdfReader, PdfWriter

from study_rag.domain import InvalidDocument, Page
from study_rag.pdf import chunk_pages, extract_pages


def test_keeps_physical_page_number_including_blank_pages(pdf_bytes):
    pages = extract_pages(pdf_bytes(["SQL relaciona tablas", "", "Python usa listas"]))
    assert [p.number for p in pages] == [1, 2, 3]
    assert pages[1].text == ""
    chunks = chunk_pages(pages)
    assert [c.page for c in chunks] == [1, 3]
    assert "Python" in chunks[1].text


def test_chunks_cover_text_with_overlap_without_crossing_pages():
    words = [f"palabra{i}" for i in range(17)]
    chunks = chunk_pages([Page(1, " ".join(words)), Page(2, "otra página")], 6, 2)
    assert [c.ordinal for c in chunks if c.page == 1] == [0, 1, 2, 3]
    assert chunks[0].text.split()[-2:] == chunks[1].text.split()[:2]
    assert set(words) == {word for c in chunks if c.page == 1 for word in c.text.split()}
    assert all(len(c.text.split()) <= 6 for c in chunks)


@pytest.mark.parametrize("data", [b"", b"not a pdf", b"%PDF-corrupt"])
def test_rejects_invalid_pdf(data):
    with pytest.raises(InvalidDocument):
        extract_pages(data)


def test_rejects_scanned_or_empty_pdf(pdf_bytes):
    with pytest.raises(InvalidDocument, match="OCR"):
        extract_pages(pdf_bytes([""]))


def test_limits_pages(pdf_bytes):
    with pytest.raises(InvalidDocument, match="entre 1 y 1"):
        extract_pages(pdf_bytes(["one", "two"]), max_pages=1)


def test_rejects_encrypted_pdf(pdf_bytes):
    from io import BytesIO

    writer = PdfWriter()
    writer.append(PdfReader(BytesIO(pdf_bytes(["secret"]))))
    writer.encrypt("password")
    buffer = BytesIO()
    writer.write(buffer)
    with pytest.raises(InvalidDocument, match="cifrados"):
        extract_pages(buffer.getvalue())


@pytest.mark.parametrize("size,overlap", [(0, 0), (5, 5), (5, -1)])
def test_rejects_invalid_chunk_configuration(size, overlap):
    with pytest.raises(ValueError):
        chunk_pages([Page(1, "text")], size, overlap)
