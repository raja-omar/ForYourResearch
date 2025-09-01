"""PDF to DOCX conversion via ConvertAPI."""

import os

import convertapi

from ..core.config import get_settings


def convert_pdf_to_docx(pdf_name: str, pdf_path: str, docx_path: str) -> None:
    """Convert a PDF file to DOCX using ConvertAPI."""
    settings = get_settings()
    convertapi.api_credentials = settings.convertapi_credentials

    os.makedirs(docx_path, exist_ok=True)
    convertapi.convert("docx", {"File": pdf_path}, from_format="pdf").save_files(
        f"{docx_path}/{pdf_name}.docx"
    )
