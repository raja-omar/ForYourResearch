"""Document processing: PDF parsing, highlighting, and markdown formatting."""

from pathlib import Path
from typing import List, Optional

import fitz  # PyMuPDF
from llama_parse import LlamaParse

from ..clients import get_openai_client
from ..config import get_settings

# --- PDF parsing (LlamaParse) ---


def get_parser(result_type: str = "markdown") -> LlamaParse:
    """Create a LlamaParse parser instance. Requires LLAMA_PARSE_API_KEY."""
    settings = get_settings()
    if not settings.llama_parse_api_key:
        raise ValueError(
            "LLAMA_PARSE_API_KEY is required for PDF parsing. "
            "Set it in your environment or .env file."
        )
    return LlamaParse(
        api_key=settings.llama_parse_api_key,
        result_type=result_type,
    )


def parse_pdf(pdf_path: str | Path) -> List:
    """Parse a PDF file and return document objects from LlamaParse."""
    return get_parser().load_data(str(pdf_path))


def parse_pdf_to_markdown_file(pdf_path: str | Path, output_path: str | Path) -> str:
    """Parse a PDF and write markdown to a file."""
    documents = parse_pdf(pdf_path)
    with open(output_path, "w", encoding="utf-8") as f:
        for doc in documents:
            f.write(doc.text)
    return str(output_path)


# --- PDF highlighting (PyMuPDF) ---


def highlight_text_in_pdf(
    pdf_path: str | Path,
    output_path: str | Path,
    search_text: str,
    note_title: str = "Note",
    note_content: Optional[str] = None,
) -> None:
    """Search for text in a PDF, add highlights, and optionally add a note."""
    doc = fitz.open(str(pdf_path))
    for page in doc:
        for inst in page.search_for(search_text):
            highlight = page.add_highlight_annot(inst)
            highlight.set_info(info={"title": note_title, "content": note_content or ""})
            highlight.update()
    doc.save(str(output_path), garbage=4, deflate=True, clean=True)
    doc.close()


def highlight_multiple_phrases(
    pdf_path: str | Path,
    output_path: str | Path,
    phrases: List[tuple[str, Optional[str]]],
) -> None:
    """Highlight multiple phrases in a PDF, each with optional note content."""
    doc = fitz.open(str(pdf_path))
    for page in doc:
        for search_text, note_content in phrases:
            for inst in page.search_for(search_text):
                highlight = page.add_highlight_annot(inst)
                highlight.set_info(info={"title": "Note", "content": note_content or ""})
                highlight.update()
    doc.save(str(output_path), garbage=4, deflate=True, clean=True)
    doc.close()


# --- Markdown formatting (LLM) ---

_FORMAT_PROMPT = """
You are an assistant responsible for cleaning up and formatting markdown content. Only output markdown content, nothing else. Do not miss out on any text, output the entire text that is passed in.
Please clean up the following markdown content and ensure that headings, lists, and text are properly structured and readable:

\"\"\"{document}\"\"\"
"""


def format_markdown(document: str) -> str:
    """Format and clean markdown content using the LLM."""
    client = get_openai_client()
    settings = get_settings()
    response = client.chat.completions.create(
        model=settings.openai_chat_model,
        messages=[
            {
                "role": "system",
                "content": "You are an assistant responsible for cleaning and formatting markdown. Make sure to format it properly with appropriate headings, bullet points, and correct text alignment.",
            },
            {"role": "user", "content": _FORMAT_PROMPT.format(document=document)},
        ],
        temperature=0,
        max_tokens=16384,
        logprobs=True,
    )
    return response.choices[0].message.content.strip()
