"""Document processing: PDF parsing, highlighting, and markdown formatting."""

from .documents import (
    format_markdown,
    get_parser,
    highlight_multiple_phrases,
    highlight_text_in_pdf,
    parse_pdf,
    parse_pdf_to_markdown_file,
)

__all__ = [
    "format_markdown",
    "get_parser",
    "highlight_multiple_phrases",
    "highlight_text_in_pdf",
    "parse_pdf",
    "parse_pdf_to_markdown_file",
]
