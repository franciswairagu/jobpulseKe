"""Safe text extraction for CV uploads.

The recommender never persists uploaded documents; callers pass the extracted
text directly into the profile builder.
"""

from pathlib import Path


class UnsupportedCVFormatError(ValueError):
    """Raised when a document type cannot be converted to text."""


def extract_text(path: str | Path) -> str:
    """Extract text from a `.txt`, `.pdf`, or `.docx` CV.

    PDF and DOCX support is optional so the core recommender remains light.
    The error tells deployers exactly which extra package to install.
    """
    document = Path(path)
    if not document.is_file():
        raise FileNotFoundError(f"CV file does not exist: {document}")
    suffix = document.suffix.lower()
    if suffix in {".txt", ".md"}:
        return document.read_text(encoding="utf-8", errors="replace")
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise UnsupportedCVFormatError("PDF support requires `pip install pypdf`.") from exc
        return "\n".join(page.extract_text() or "" for page in PdfReader(str(document)).pages)
    if suffix == ".docx":
        try:
            from docx import Document
        except ImportError as exc:
            raise UnsupportedCVFormatError("DOCX support requires `pip install python-docx`.") from exc
        return "\n".join(paragraph.text for paragraph in Document(str(document)).paragraphs)
    raise UnsupportedCVFormatError("Supported CV formats are .txt, .pdf, and .docx.")
