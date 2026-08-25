from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.models import User
from app.utils.security import require_student
from app.services.knowledge_graph import build_graph, node_detail

router = APIRouter(prefix="/api/knowledge-graph", tags=["knowledge-graph"])


@router.get("")
def get_graph(subject_id: int = None, user: User = Depends(require_student), db: Session = Depends(get_db)):
    return build_graph(db, user.id, subject_id)


@router.get("/node/{topic_id}")
def get_node(topic_id: int, user: User = Depends(require_student), db: Session = Depends(get_db)):
    detail = node_detail(db, user.id, topic_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Topic not found")
    return detail
