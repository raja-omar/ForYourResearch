from sqlalchemy.orm import Session
from sqlalchemy import and_
from ..models.search import SearchCreate
from ..schemas.search import Search as SearchSchema
from ..schemas.search_result_title_abstract import (
    SearchResultTitleAbstract as SearchResultTitleAbstractSchema,
)


def save_query(db: Session, search_create: SearchCreate):

    all_search_query_tuples = retrieve_all_queries(db, search_create.uid)

    search_query_list = convert_to_list(all_search_query_tuples)
    base_search_query = search_create.search_query + " ⦿ "

    max_number = 0
    for search_query in search_query_list:
        if search_query.startswith(base_search_query):
            number_part = search_query.split(" ⦿ ")[1]
            number = int(number_part)
            if number > max_number:
                max_number = number

    new_number = max_number + 1
    unique_search_query = f"{base_search_query}{new_number}"
    row = SearchSchema(uid=search_create.uid, search_query=unique_search_query)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def save_papers(db: Session, papers: list, search_id: int):
    # Extract all paperIds from the incoming list of papers
    paper_ids = [paper["paperId"] for paper in papers]

    # Query the database once for all papers with matching paperId and search_id
    existing_papers = (
        db.query(SearchResultTitleAbstractSchema)
        .filter(
            SearchResultTitleAbstractSchema.paperId.in_(paper_ids),
            SearchResultTitleAbstractSchema.search_id == search_id,
        )
        .all()
    )

    # Create a dictionary of existing papers keyed by paperId for quick lookups
    existing_papers_dict = {paper.paperId: paper for paper in existing_papers}

    papers_to_add = []
    for paper in papers:
        if paper["paperId"] in existing_papers_dict:
            # Update the existing paper
            existing_paper = existing_papers_dict[paper["paperId"]]
            existing_paper.title_relevance = paper["title_relevance"]
            existing_paper.abstract_relevance = paper["abstract_relevance"]
            existing_paper.title = paper["title"]
            existing_paper.year = paper["year"]
            existing_paper.abstract = paper["abstract"]
            existing_paper.url = (
                paper["openAccessPdf"]["url"] if paper.get("openAccessPdf") else None
            )
        else:
            # Add the new paper if it doesn't exist
            new_paper = SearchResultTitleAbstractSchema(
                search_id=search_id,
                title=paper["title"],
                year=paper["year"],
                abstract=paper["abstract"],
                title_relevance=paper["title_relevance"],
                abstract_relevance=paper["abstract_relevance"],
                paperId=paper["paperId"],
                url=(
                    paper["openAccessPdf"]["url"]
                    if paper.get("openAccessPdf")
                    else None
                ),
            )
            papers_to_add.append(new_paper)

    # Bulk insert new papers
    if papers_to_add:
        db.add_all(papers_to_add)

    # Commit the transaction after updates and inserts
    db.commit()


def convert_to_list(queries):
    queries_list = []
    for (query,) in queries:
        queries_list.append(query)
    return queries_list


def retrieve_all_queries(db: Session, uid: str):

    return db.query(SearchSchema.search_query).filter(SearchSchema.uid == uid).all()


def find_search_id(db: Session, uid: str, search_query: str):
    "method to find search id for retreive_papers_by_query method"

    response = (
        db.query(SearchSchema.search_id)
        .filter(
            and_(SearchSchema.uid == uid, SearchSchema.search_query == search_query)
        )
        .all()
    )

    search_id = response[0][0]
    return search_id


def retrieve_papers_by_query(db: Session, search_id: int):
    # instead of using composite key of (uid+ searchQuery) we create a new field search_id which maps to user uid + searchQuery

    return (
        db.query(SearchResultTitleAbstractSchema)
        .filter(SearchResultTitleAbstractSchema.search_id == search_id)
        .all()
    )


def update_manual_paper_relevance(
    db: Session, search_id: int, title: str, relevance_value: str, relevance_type: str
):
    # functions gets a specific query for a specific user by using search id and then helps change the manual relevance

    # search id maps: user and searchquery
    # title : maps to specific paper
    # manualrelevancevalue : relevance value send from frontend

    paper = (
        db.query(SearchResultTitleAbstractSchema)
        .filter(
            and_(
                SearchResultTitleAbstractSchema.search_id == search_id,
                SearchResultTitleAbstractSchema.title == title,
            )
        )
        .first()
    )

    if relevance_type == "title_relevance":
        paper.title_relevance = relevance_value
    elif relevance_type == "abstract_relevance":
        paper.abstract_relevance = relevance_value

    db.commit()
