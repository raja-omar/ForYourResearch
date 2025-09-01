"""Pinecone-based reranking of documents by query relevance."""

from typing import TYPE_CHECKING, List, Tuple

from pinecone.grpc import PineconeGRPC

from .config import get_settings

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def rerank(query: str, docs: List[str]) -> Tuple[List, str]:
    """Rerank documents by relevance to the query using Pinecone's reranker.

    Processes documents in chunks of 100 (Pinecone limit) and returns
    results sorted by score descending.

    Args:
        query: Search query string.
        docs: List of document/abstract strings to rerank.

    Returns:
        Tuple of (reranked docs with scores, modified query string).
    """
    settings = get_settings()
    pc = PineconeGRPC(api_key=settings.pinecone_api_key)

    removed_quotes_query = (
        query.replace('"', "")
        .replace("(", "")
        .replace(")", "")
        .replace("AND", "and")
        .replace("OR", "or")
    )
    modified_query = f"Does this abstract have any contextual information about {removed_quotes_query}?"

    reranked_docs = []
    for i in range(0, len(docs), 100):
        chunk = docs[i : i + 100]
        reranked_chunk = pc.inference.rerank(
            model=settings.pinecone_rerank_model,
            query=modified_query,
            documents=chunk,
            parameters={"truncate": "END"},
            return_documents=True,
        )
        reranked_docs.extend(reranked_chunk.data)

    reranked_docs.sort(key=lambda x: x["score"], reverse=True)
    return reranked_docs, modified_query


def save_titles_to_visualize_reranked_title_table(
    reranked_docs: list,
    search_query: str,
    db: "Session",
    uid: str = "123",
) -> None:
    """Save high-scoring reranked titles to the visualization table.

    Args:
        reranked_docs: Output from rerank().
        search_query: The search query.
        db: Database session (required for persistence).
        uid: User ID (default "123").
    """
    from backend.app.crud import visualise_data_operations

    most_relevant_titles = []
    for reranked_title in reranked_docs:
        if reranked_title["score"] > 0.90:
            most_relevant_titles.append(
                {
                    "title": reranked_title.document.text,
                    "score": reranked_title.score,
                }
            )
    visualise_data_operations.save_to_visualise_reranked_title_table(
        uid=uid,
        query=search_query,
        titles=most_relevant_titles,
        db=db,
    )
