from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..dependencies import get_db
from ..schemas.visualise_reranked_title import VisualiseRerankedTitle


def save_to_visualise_reranked_title_table(
    uid: str, query: str, titles: list, db: Session = Depends(get_db)
):

    #
    # Reranking.py
    #

    titles_to_add = []
    for reranked_title in titles:
        row = VisualiseRerankedTitle(
            uid=uid,
            query=query,
            score=reranked_title["score"],
            title=reranked_title["title"],
        )

        titles_to_add.append(row)
    db.add_all(titles_to_add)
    db.commit()
