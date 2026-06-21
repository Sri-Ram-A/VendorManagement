# clients/docling.py

from docling.document_converter import DocumentConverter

_converter = None


def get_converter():
    global _converter
    if _converter is None:
        _converter = DocumentConverter()
    return _converter
