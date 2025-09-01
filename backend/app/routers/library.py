from fastapi import APIRouter
from ..util import helper_functions
from ..models.search import SearchCreate, Search
from ..models.request_with_list import RequestObjectWithListData
from ..models.request_with_uid_and_query import RequestWithUidAndQuery
from ..models.request_with_search_id_title_and_relevance_value import (
    RequestWithSearchIdTitleRelevanceValue,
)


from fastapi import Depends
from sqlalchemy.orm import Session
from ..dependencies import get_db
from ..crud import library_operations

router = APIRouter()
suffix = ""

if helper_functions.is_in_production():
    suffix = "/"


@router.post(f"/saveQuery", response_model=SearchCreate)
def save_query(request_model: SearchCreate, db: Session = Depends(get_db)):
    return library_operations.save_query(search_create=request_model, db=db)


"""
to be implemented after i come to the lab.

currently it accepts the paper array but only stores the uid and 
search query to the Search table. need to add functionality
to store a row in the search_result table. row_ref.search_id is
the primary key of the row created in Search table.
"""


@router.post(f"/saveToLibrary", response_model=Search)
def save_to_library(
    request_model: RequestObjectWithListData, db: Session = Depends(get_db)
):
    """
    To-do: Before saving the query to database, we need to check if
    the query already exists with the user's uid so we can add
    a number next to the query like we do in firebase.
    """
    search_row = SearchCreate(
        uid=request_model.uid, search_query=request_model.searchQuery
    )
    row_ref = library_operations.save_query(search_create=search_row, db=db)

    library_operations.save_papers(
        papers=request_model.data, db=db, search_id=row_ref.search_id
    )
    return row_ref


@router.get(f"/fetchAllQueries")
def fetch_all_queries(uid: str, db: Session = Depends(get_db)):
    list_queries = library_operations.convert_to_list(
        library_operations.retrieve_all_queries(db=db, uid=uid)
    )
    return list_queries


@router.post(f"/fetchPapersRelatedToQuery")
def fetch_papers_related_to_query(
    request_model: RequestWithUidAndQuery, db: Session = Depends(get_db)
):
    papers_list = []
    search_id = library_operations.find_search_id(
        uid=request_model.uid, search_query=request_model.search_query, db=db
    )

    papers_related_to_query = library_operations.retrieve_papers_by_query(
        search_id=search_id, db=db
    )
    for paper in papers_related_to_query:
        papers_list.append(
            {
                "title": paper.title,
                "abstract": paper.abstract,
                "url": paper.url,
                "paperId": paper.paperId,
                "year": paper.year,
                "title_relevance": paper.title_relevance,
                "abstract_relevance": paper.abstract_relevance,
            }
        )
    return papers_list


@router.post(f"/updatePaperRelevance")
def update_paper_relevance(
    request_model: RequestWithSearchIdTitleRelevanceValue, db: Session = Depends(get_db)
):
    search_id = library_operations.find_search_id(
        db=db, uid=request_model.uid, search_query=request_model.search_query
    )
    # print(search_id)
    # print(request_model.title)
    library_operations.update_manual_paper_relevance(
        db=db,
        search_id=search_id,
        title=request_model.title,
        relevance_value=request_model.relevance_value,
        relevance_type=request_model.relevance_type,
    )
