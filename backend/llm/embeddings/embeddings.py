"""Embedding generation, vector records, and Pinecone indexing."""

import hashlib
import json
from typing import List

from pinecone import Pinecone, ServerlessSpec

from ..clients import get_openai_client
from ..config import get_settings


def generate_embedding_for_text(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for a list of texts."""
    client = get_openai_client()
    settings = get_settings()
    response = client.embeddings.create(
        input=texts,
        model=settings.openai_embedding_model,
    )
    return [item.embedding for item in response.data]


def generate_embedding_for_query(
    text: str,
    pc: Pinecone,
) -> tuple[List[float], str]:
    """Generate embedding for a search query with boolean operator preprocessing."""
    client = get_openai_client()
    settings = get_settings()
    keywords = (
        text.replace("(", "")
        .replace(")", "")
        .replace('"', "")
        .replace(" OR ", " ")
        .replace(" AND ", " ")
        .split()
    )
    keywords_to_feed = " ".join(keywords)
    response = client.embeddings.create(
        input=keywords_to_feed,
        model=settings.openai_embedding_model,
    )
    return response.data[0].embedding, keywords_to_feed


def generate_records(
    texts: List[str],
    user_id: str,
    search_query: str,
    pc: Pinecone,
) -> List[dict]:
    """Create Pinecone records with embeddings and metadata."""
    records = []
    embeddings = generate_embedding_for_text(texts)
    for text, embedding in zip(texts, embeddings):
        hashed_id = hashlib.sha256(text.encode("utf-8")).hexdigest()
        records.append(
            {
                "id": hashed_id,
                "values": embedding,
                "metadata": {
                    "user_id": user_id,
                    "search_query": search_query,
                    "text": text,
                },
            }
        )
    return records


def retrieve_top_k_records(
    pc: Pinecone,
    embedding_for_query: List[float],
    index_name: str,
    user_id: str,
    search_query: str,
    top_k: int,
):
    """Query Pinecone for top-k records matching the query embedding."""
    index = pc.Index(index_name)
    return index.query(
        vector=embedding_for_query,
        top_k=top_k,
        include_metadata=True,
        filter={"user_id": user_id, "search_query": search_query},
    )


def create_index(pc: Pinecone, index_name: str, dimension: int = 3072) -> None:
    """Create a new Pinecone index if it does not exist."""
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )


def upsert_records(pc: Pinecone, records: list, index_name: str) -> None:
    """Upsert a batch of records to a Pinecone index."""
    index = pc.Index(index_name)
    index.upsert(records)


def get_titles_from_json(file_path: str) -> List[str]:
    """Load paper titles from a JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        papers = json.load(f)
    return [paper["title"] for paper in papers]
