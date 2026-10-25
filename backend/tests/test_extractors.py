from io import BytesIO

import fitz
import pytest
from docx import Document

from app.processing.extractors.docx_extractor import DocxExtractor
from app.processing.extractors.factory import UnsupportedFileTypeError, get_extractor
from app.processing.extractors.pdf_extractor import PdfExtractor
from app.processing.extractors.txt_extractor import TxtExtractor


def make_pdf(*pages: str) -> bytes:
    with fitz.open() as pdf:
        for text in pages:
            page = pdf.new_page()
            if text:
                page.insert_text((72, 72), text)
        return pdf.tobytes()


def make_docx(*paragraphs: str) -> bytes:
    doc = Document()
    for text in paragraphs:
        doc.add_paragraph(text)
    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def test_pdf_keeps_page_numbers_and_skips_blank_pages():
    result = PdfExtractor().extract("a.pdf", make_pdf("first", "", "third"))
    assert [(n, t) for n, t in result.pages] == [(1, "first"), (3, "third")]
    assert result.text == "first\n\nthird"


def test_docx_joins_non_empty_paragraphs():
    result = DocxExtractor().extract("a.docx", make_docx("one", "  ", "two"))
    assert result.text == "one\ntwo"
    assert result.pages == [(1, "one\ntwo")]


def test_txt_decodes_utf8_and_ignores_bad_bytes():
    result = TxtExtractor().extract("a.txt", "café".encode() + b"\xff")
    assert result.text == "café"


def test_empty_txt_has_no_pages():
    assert TxtExtractor().extract("a.txt", b"  ").pages == []


@pytest.mark.parametrize(
    ("name", "cls"),
    [("a.pdf", PdfExtractor), ("A.DOCX", DocxExtractor), ("a.txt", TxtExtractor)],
)
def test_factory_picks_extractor_by_extension(name, cls):
    assert isinstance(get_extractor(name), cls)


@pytest.mark.parametrize("name", ["a.doc", "a.exe", "noext"])
def test_factory_rejects_unsupported(name):
    with pytest.raises(UnsupportedFileTypeError):
        get_extractor(name)
