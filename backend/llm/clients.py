"""Shared LLM API clients.

Clients are lazily initialized to avoid loading config at import time.
"""

from functools import lru_cache
from typing import TYPE_CHECKING

from openai import OpenAI

if TYPE_CHECKING:
    from .config import Settings


@lru_cache(maxsize=1)
def get_openai_client() -> OpenAI:
    """Return a cached OpenAI client instance."""
    from .config import get_settings

    settings = get_settings()
    return OpenAI(api_key=settings.openai_api_key)
