"""Semantic Scholar search and current results endpoints."""

import time
from typing import Any

import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..crud import current_search_result_operations
from ..dependencies import get_db
from ..models.request_with_list import RequestObjectWithListData
from ..util.helper_functions import filter_papers, parse_query
from ..core.config import get_settings

router = APIRouter()


@router.get("/search")
async def search(query: str) -> dict[str, Any]:
    """Search Semantic Scholar for papers matching the query."""
    settings = get_settings()
    url = "https://api.semanticscholar.org/graph/v1/paper/search/"
    headers = {"x-api-key": settings.semanticscholar_api_key}

    parsed_query = parse_query(query)
    total_papers = []
    total_offset = 0
    limit = 100
    number_of_papers = 0

    while total_offset < 1000:
        query_params = {
            "query": parsed_query,
            "limit": limit,
            "fields": "title,abstract,year,openAccessPdf,isOpenAccess",
            "offset": total_offset,
        }
        time.sleep(2)
        response = requests.get(url, params=query_params, headers=headers)
        response_data = response.json()
        number_of_papers = response_data["total"]
        papers = response_data.get("data", [])
        total_papers.extend(papers)
        total_offset += limit
        if len(papers) < limit:
            break

    for paper in total_papers:
        paper["Relevance"] = "Untagged"

    total_papers = filter_papers(total_papers)
    return {"papers": total_papers, "number_of_papers": number_of_papers}


@router.post("/saveCurrentSearchResults")
def save_current_search_results(
    request_model: RequestObjectWithListData, db: Session = Depends(get_db)
) -> None:
    """Save current search results for a user."""
    try:
        current_search_result_operations.save_current_search_results(
            db=db, papers=request_model.data, uid=request_model.uid
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/getCurrentSearchResults")
def get_current_search_results(uid: str, db: Session = Depends(get_db)):
    """Retrieve current search results for a user."""
    return current_search_result_operations.get_current_search_results(
        db=db, uid=uid
    )
