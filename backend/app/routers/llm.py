"""LLM endpoints: screening, research questions, markdown/HTML retrieval."""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..crud.full_text_operations import read_pdfs_from_s3, upload_papers_to_s3
from ..dependencies import get_db
from ..models.request_for_html import RequestForHtml
from ..models.request_for_md import RequestForMd
from ..models.request_for_rq import RequestObjectForRQ
from ..models.request_with_list import RequestObjectWithListData
from ..pdf_parsing.html_to_text import process_html_files
from ...llm.screening import filter_relevant_abstracts, screen_papers, screen_titles

router = APIRouter()


def _pdf_base_path() -> Path:
    """Base path for PDF parsing output directories."""
    from ..core.config import get_settings

    return get_settings().pdf_base_path


@router.post("/screenTitlesAndAbstracts")
def screen_titles_and_abstracts(
    request: RequestObjectWithListData, db: Session = Depends(get_db)
):
    """Screen paper titles and abstracts for relevance to the search query."""
    paper_titles = [paper["title"] for paper in request.data]
    titles_set = screen_titles(paper_titles, request.searchQuery)
    papers = request.data
    relevant_abstracts = []

    for paper in papers:
        if paper["title"] in titles_set:
            paper["title_relevance"] = "Relevant"
            if paper.get("abstract") and len(paper["abstract"]) > 0:
                relevant_abstracts.append(paper["abstract"])
        else:
            paper["title_relevance"] = "Irrelevant"

    screened_abstracts = filter_relevant_abstracts(
        request.searchQuery, relevant_abstracts
    )
    reranked_abstracts_set = set(screened_abstracts)

    for paper in papers:
        paper["abstract_relevance"] = (
            "Relevant" if paper.get("abstract") in reranked_abstracts_set else "Irrelevant"
        )

    return papers


@router.post("/screenForResearchQuestions")
def screen_for_research_questions(request: RequestObjectForRQ):
    """Screen papers for research question answers; upload PDFs, convert to HTML, extract citations."""
    papers_with_links = [
        {"title": p["title"], "link": p["openAccessPdf"]["url"]}
        for p in request.data
        if p.get("isOpenAccess")
        and p.get("openAccessPdf")
        and p["openAccessPdf"].get("url")
    ]

    base = _pdf_base_path()
    html_path = str(base / "html_files" / request.uid / request.searchQuery)
    upload_papers_to_s3(request.uid, request.searchQuery, request.data)
    paper_titles = read_pdfs_from_s3(request.uid, request.searchQuery, html_path)
    papers = process_html_files(html_path, paper_titles)

    return screen_papers(
        research_questions=request.researchQuestions,
        papers=papers,
    )


@router.post("/getMarkdown")
def get_markdown(request: RequestForMd) -> str:
    """Return markdown content for a paper."""
    base = _pdf_base_path()
    if request.uid:
        folder_path = base / "split_mds" / request.uid / request.search_query
    else:
        folder_path = base / "split_mds" / request.search_query
    title = request.title.replace(".pdf", "")
    file_path = folder_path / f"{title}.md"

    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Markdown file not found")
    try:
        return file_path.read_text(encoding="utf-8")
    except OSError:
        raise HTTPException(status_code=500, detail="Error reading markdown file")


@router.post("/getHtml")
def get_html(request: RequestForHtml) -> str:
    """Return HTML content for a paper."""
    base = _pdf_base_path()
    folder_path = base / "html_files" / request.uid / request.search_query
    title = request.title.replace(".pdf", "").replace(".html", "")
    file_path = folder_path / f"{title}.html"

    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="HTML file not found")
    try:
        return file_path.read_text(encoding="utf-8")
    except OSError as e:
        raise HTTPException(status_code=500, detail="Error reading HTML file")
