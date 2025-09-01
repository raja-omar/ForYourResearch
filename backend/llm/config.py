"""Centralized configuration for LLM-related services.

All API keys and secrets are loaded from environment variables.
Create a .env file in the project root with the required keys.
"""

import os
from functools import lru_cache
from typing import Optional

# Load .env from project root when python-dotenv is available
try:
    from pathlib import Path

    from dotenv import load_dotenv

    _env_paths = [
        Path(__file__).resolve().parent.parent / ".env",  # backend/.env
        Path(__file__).resolve().parent.parent.parent / ".env",  # project root
    ]
    for p in _env_paths:
        if p.exists():
            load_dotenv(p)
            break
    else:
        load_dotenv()
except ImportError:
    pass  # python-dotenv not installed; rely on env vars


def _get(key: str, default: Optional[str] = None) -> str:
    value = os.getenv(key, default or "")
    if not value and default is None:
        raise ValueError(
            f"Missing required environment variable: {key}. "
            "Set it in your environment or .env file."
        )
    return value


@lru_cache(maxsize=1)
def get_settings() -> "Settings":
    """Return cached settings instance."""
    return Settings()


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self) -> None:
        self.openai_api_key = _get("OPENAI_API_KEY")
        self.pinecone_api_key = _get("PINECONE_API_KEY")
        self.llama_parse_api_key = os.getenv("LLAMA_PARSE_API_KEY") or None
        self.openai_embedding_model = os.getenv(
            "OPENAI_EMBEDDING_MODEL", "text-embedding-3-large"
        )
        self.openai_chat_model = os.getenv(
            "OPENAI_CHAT_MODEL", "gpt-4o-mini"
        )
        self.pinecone_rerank_model = os.getenv(
            "PINECONE_RERANK_MODEL", "bge-reranker-v2-m3"
        )
