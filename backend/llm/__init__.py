"""LLM utilities for embeddings, screening, reranking, and document processing."""

from .config import get_settings
from .documents import (
    format_markdown,
    get_parser,
    highlight_multiple_phrases,
    highlight_text_in_pdf,
    parse_pdf,
    parse_pdf_to_markdown_file,
)
from .embeddings import (
    create_index,
    generate_embedding_for_query,
    generate_embedding_for_text,
    generate_records,
    get_titles_from_json,
    retrieve_top_k_records,
    upsert_records,
)
from .reranking import rerank, save_titles_to_visualize_reranked_title_table
from .screening import (
    clean_text,
    document_relevance,
    filter_relevant_abstracts,
    get_rq_answers,
    read_md_files,
    screen_individual_paper,
    screen_papers,
    screen_titles,
)

__all__ = [
    "clean_text",
    "create_index",
    "document_relevance",
    "filter_relevant_abstracts",
    "format_markdown",
    "generate_embedding_for_query",
    "generate_embedding_for_text",
    "generate_records",
    "get_parser",
    "get_rq_answers",
    "get_settings",
    "get_titles_from_json",
    "highlight_multiple_phrases",
    "highlight_text_in_pdf",
    "parse_pdf",
    "parse_pdf_to_markdown_file",
    "read_md_files",
    "rerank",
    "retrieve_top_k_records",
    "save_titles_to_visualize_reranked_title_table",
    "screen_individual_paper",
    "screen_papers",
    "screen_titles",
    "upsert_records",
]
