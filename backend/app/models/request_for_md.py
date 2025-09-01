from typing import Optional

from pydantic import BaseModel


class RequestForMd(BaseModel):
    title: str
    search_query: str
    uid: Optional[str] = None  # Required for path; fallback for backward compat
