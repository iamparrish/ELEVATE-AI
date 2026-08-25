from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.models import User, Recommendation
from app.schemas.schemas import RecommendationReviewIn
from app.utils.security import require_teacher
from app.services import teacher_service as ts

router = APIRouter(prefix="/api/teacher", tags=["teacher"])


@router.get("/students")
def students(user: User = Depends(require_teacher), db: Session = Depends(get_db)):
    return {"students": ts.list_students(db)}


@router.get("/students/{student_id}")
def student_detail(student_id: int, user: User = Depends(require_teacher), db: Session = Depends(get_db)):
    detail = ts.student_detail(db, student_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Student not found")
    return detail


@router.get("/analytics")
def analytics(user: User = Depends(require_teacher), db: Session = Depends(get_db)):
    return ts.class_analytics(db)


@router.get("/recommendations")
def recommendations(user: User = Depends(require_teacher), db: Session = Depends(get_db)):
    recs = db.query(Recommendation).filter(Recommendation.status == "active").order_by(Recommendation.priority.desc()).limit(50).all()
    from app.models.models import Topic, User as U
    out = []
    for r in recs:
        student = db.query(U).filter(U.id == r.student_id).first()
        topic = db.query(Topic).filter(Topic.id == r.topic_id).first() if r.topic_id else None
        out.append({
            "id": r.id, "student_name": student.full_name if student else "Unknown",
            "student_id": r.student_id, "title": r.title, "reason": r.reason, "type": r.rec_type,
            "topic_name": topic.name if topic else None, "review_status": r.teacher_review_status,
        })
    return {"recommendations": out}


@router.post("/recommendations/{rec_id}/review")
def review(rec_id: int, body: RecommendationReviewIn, user: User = Depends(require_teacher), db: Session = Depends(get_db)):
    rec = ts.review_recommendation(db, rec_id, body.action)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return {"message": f"Recommendation {body.action}d", "status": rec.teacher_review_status}
