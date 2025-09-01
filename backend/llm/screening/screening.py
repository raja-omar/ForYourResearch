"""Relevance screening: titles, abstracts, documents, and full papers.

Provides screening at multiple levels:
- Titles: screen_titles
- Abstracts: filter_relevant_abstracts
- Documents: document_relevance, get_rq_answers
- Full papers: screen_papers, screen_individual_paper
"""

import os
import re
from typing import Any, Dict, List, Set

from pydantic import BaseModel

from ..clients import get_openai_client
from ..config import get_settings

# --- Prompts ---
_TITLE_PROMPT = """
You are an Assistant responsible for helping determine whether the title of a paper is relevant to the query. This is the systematic step to check it:
1. Check if the title contains at least 50 percent of the words in the query that are after and before the AND operator. If it does, output "Yes" and stop.
2. If the title does not contain at least 50 percent of the words in the query that are after and before the AND operator, check if the title has synonyms for the words which are not in query. If including synonyms the total percentage is more than 50, output "Yes" and stop.
3. If the title does not contain at least 50 percent of the words in the query that are after and before the AND operator and does not have any synonyms for the words which are not in query, output "No" and stop.

Query: {query}
Title: {title}
Respond only with 'Yes' or 'No'.
"""

_DOCUMENT_RELEVANCE_PROMPT = """
You are a scientific Assistant responsible for determining if the provided document fully answers the given query, treating the document as evidence. If the document evidently answers the question, output "Yes". If not, output "No".
Query: {query}
Document: \"\"\"{document}\"\"\"
Answer:
"""


class CitationsResponse(BaseModel):
    citations: List[str]


# --- Title screening ---
def screen_titles(titles: List[str], query: str) -> Set[str]:
    """Check relevance of document titles to a query."""
    client = get_openai_client()
    settings = get_settings()
    relevant_titles: Set[str] = set()
    for title in titles:
        response = client.chat.completions.create(
            model=settings.openai_chat_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an Assistant responsible for helping detect whether the retrieved document is relevant to the query.",
                },
                {"role": "user", "content": _TITLE_PROMPT.format(query=query, title=title)},
            ],
            temperature=0,
        )
        if response.choices[0].message.content.strip().lower() == "yes":
            relevant_titles.add(title)
    return relevant_titles


# --- Abstract screening ---
def filter_relevant_abstracts(search_query: str, abstracts: List[str]) -> List[str]:
    """Filter abstracts to those relevant to the search query."""
    client = get_openai_client()
    settings = get_settings()
    relevant = []
    for abstract in abstracts:
        try:
            response = client.beta.chat.completions.parse(
                model=settings.openai_chat_model,
                temperature=0,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an assistant that checks if a search query is relevant to an abstract.",
                    },
                    {
                        "role": "user",
                        "content": f"Does the abstract: '{abstract}' answer in the context related to the search query: {search_query}? Respond with 'yes' if it does, or 'no' if it does not. Respond with 'yes' if you are not sure.",
                    },
                ],
            )
            if response.choices[0].message.content.strip().lower() == "yes":
                relevant.append(abstract)
        except Exception:
            continue
    return relevant


# --- Document relevance ---
def document_relevance(queries: List[str], documents: List[dict]) -> List[dict]:
    """Determine which documents answer each query."""
    client = get_openai_client()
    settings = get_settings()
    result = []
    for query in queries:
        relevant_docs = []
        for doc in documents:
            title = doc.get("title", "").replace(".md", "")
            full_text = doc.get("full_text", "")
            response = client.beta.chat.completions.parse(
                model=settings.openai_chat_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an Assistant responsible for answering questions based strictly on the provided text. If the text contains an answer in context of the question, respond with 'Yes'. If the text does not answer the question, respond with 'No'.",
                    },
                    {
                        "role": "user",
                        "content": _DOCUMENT_RELEVANCE_PROMPT.format(query=query, document=full_text),
                    },
                ],
                temperature=0,
            )
            if response.choices[0].message.content.strip() == "Yes":
                relevant_docs.append(title)
        result.append({query: relevant_docs})
    return result


def get_rq_answers(
    paper_titles: List[str],
    queries: List[str],
    documents: List[Dict[str, str]],
) -> List[Dict[str, Any]]:
    """Extract answers to research questions from documents with cited segments."""
    client = get_openai_client()
    settings = get_settings()
    system_prompt = (
        "You are an Assistant responsible for answering questions based strictly on the provided text. "
        "If the text contains an answer in context of the question, respond with 'Yes' followed by first fullstop of all "
        "text segments that answer the question as an array, enclosed in quotation marks. If the text does not answer "
        "the question, respond with 'No answer found.'"
    )
    results = []
    for paper_title, document in zip(paper_titles, documents):
        paper_data: Dict[str, Any] = {paper_title: {}}
        full_text = document.get("full_text", document.get("text", ""))
        for query in queries:
            try:
                response = client.beta.chat.completions.parse(
                    model=settings.openai_chat_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"{query} based on: {full_text}"},
                    ],
                    max_completion_tokens=16384,
                    temperature=0,
                )
                answer = response.choices[0].message.content.strip()
                if "Yes" in answer:
                    segments = [
                        s.strip('"').replace('\\"', "").strip()
                        for s in answer.replace("Yes", "").strip("[]").split(", ")
                    ]
                    if segments:
                        segments[0] = segments[0].lstrip("[").strip('"').strip()
                    paper_data[paper_title][query] = segments
                else:
                    paper_data[paper_title][query] = ["No answer found."]
            except Exception:
                paper_data[paper_title][query] = ["No answer found."]
        results.append(paper_data)
    return results


def clean_text(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Clean JSON artifacts from extracted text segments."""
    pattern = r'\{"choices":\[\{"content":" |\\"|\\'

    def clean_string(t: str) -> str:
        t = re.sub(pattern, "", t)
        t = re.sub(r'"}]}$', "", t)
        t = re.sub(r"^\[|\]$", "", t)
        return t.strip()

    for item in data:
        for value in item.values():
            for key, text_list in value.items():
                value[key] = [clean_string(t) for t in text_list]
    return data


# --- Full paper screening (chunked citation extraction) ---
def _chunk_document(document: str, max_chunk_size: int) -> List[tuple[int, str]]:
    words = document.split()
    chunks, current, size, cid = [], [], 0, 1
    for word in words:
        size += len(word) + 1
        if size > max_chunk_size:
            chunks.append((cid, " ".join(current)))
            current, size, cid = [word], len(word) + 1, cid + 1
        else:
            current.append(word)
    if current:
        chunks.append((cid, " ".join(current)))
    return chunks


def screen_individual_paper(
    queries: List[str],
    title: str,
    document: str,
    max_chunk_size: int = 20000,
) -> Dict[str, Dict[str, List[str]]]:
    """Extract cited passages from a paper for each research question."""
    client = get_openai_client()
    settings = get_settings()
    result: Dict[str, Dict[str, List[str]]] = {title: {}}
    chunks = _chunk_document(document, max_chunk_size)
    system_prompt = (
        "You will be provided with a document delimited by triple quotes and a question. "
        "Your task is to answer the question using only the provided document and matching word to word to cite "
        "the passage(s) of the document used to answer the question, do not add additional content by yourself. "
        'If the document does not contain the information needed to answer this question then simply write: "No answer found". '
        'If an answer to the question is provided, it must be annotated with a citation. Use the following format to cite relevant passages ({"citation": …}).'
    )
    for query in queries:
        highlighted: List[str] = []
        for _, chunk in chunks:
            response = client.beta.chat.completions.parse(
                model=settings.openai_chat_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Document: '''{chunk}'''\nQuestion: {query}"},
                ],
                max_completion_tokens=1000,
                temperature=0,
                response_format=CitationsResponse,
            )
            citations = response.choices[0].message.parsed.citations
            if "No answer found" not in str(citations):
                highlighted.extend(citations)
        result[title][query] = highlighted if highlighted else ["No answer found."]
    return result


def screen_papers(
    research_questions: List[str],
    papers: List[Dict[str, Any]],
    max_chunk_size: int = 10000,
) -> List[Dict[str, Any]]:
    """Screen multiple papers for research question answers."""
    results = []
    for paper in papers:
        title = paper.get("title", "").replace(".html", "")
        full_text = paper.get("full_text", "")
        results.append(
            screen_individual_paper(
                queries=research_questions,
                title=title,
                document=full_text,
                max_chunk_size=max_chunk_size,
            )
        )
    return results


def read_md_files(directory_path: str) -> List[str]:
    """Read all .md files from a directory."""
    contents = []
    for filename in os.listdir(directory_path):
        if filename.endswith(".md"):
            try:
                with open(os.path.join(directory_path, filename), "r", encoding="utf-8") as f:
                    contents.append(f.read())
            except OSError:
                continue
    return contents
