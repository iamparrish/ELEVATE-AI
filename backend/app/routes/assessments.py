from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.models import User, Assessment, AssessmentAttempt, Topic
from app.schemas.schemas import AssessmentBuildIn, AssessmentSubmitIn
from app.utils.security import require_student
from app.services.assessment_engine import build_assessment, get_assessment_payload, submit_assessment

router = APIRouter(prefix="/api/assessments", tags=["assessments"])


@router.get("")
def list_assessments(user: User = Depends(require_student), db: Session = Depends(get_db)):
    assessments = db.query(Assessment).filter(Assessment.student_id == user.id).order_by(Assessment.created_at.desc()).limit(20).all()
    out = []
    for a in assessments:
        attempt = db.query(AssessmentAttempt).filter(AssessmentAttempt.assessment_id == a.id, AssessmentAttempt.status == "completed").order_by(AssessmentAttempt.submitted_at.desc()).first()
        out.append({
            "id": a.id, "title": a.title, "type": a.assessment_type,
            "num_questions": len(a.question_ids or []), "time_limit_minutes": a.time_limit_minutes,
            "created_at": a.created_at.isoformat(), "score": attempt.score if attempt else None,
            "completed": attempt is not None,
        })
    return {"assessments": out}


@router.post("/build")
def build(body: AssessmentBuildIn, user: User = Depends(require_student), db: Session = Depends(get_db)):
    assessment = build_assessment(db, user.id, body.assessment_type, subject_id=body.subject_id,
                                   topic_id=body.topic_id, num_questions=body.num_questions)
    if not assessment.question_ids:
        raise HTTPException(status_code=400, detail="Not enough content for this assessment yet.")
    return {"assessment_id": assessment.id, "title": assessment.title, "time_limit_minutes": assessment.time_limit_minutes,
            "questions": get_assessment_payload(db, assessment)}


@router.get("/{assessment_id}")
def get_assessment(assessment_id: int, user: User = Depends(require_student), db: Session = Depends(get_db)):
    a = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return {"assessment_id": a.id, "title": a.title, "time_limit_minutes": a.time_limit_minutes,
            "questions": get_assessment_payload(db, a)}


@router.post("/{assessment_id}/submit")
def submit(assessment_id: int, body: AssessmentSubmitIn, user: User = Depends(require_student), db: Session = Depends(get_db)):
    a = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Assessment not found")
    from app.models.models import Question
    answers = []
    for ans in body.answers:
        q = db.query(Question).filter(Question.id == ans.question_id).first()
        answers.append({
            "question_id": ans.question_id, "selected_index": ans.selected_index,
            "topic_id": ans.topic_id or (q.topic_id if q else None), "marked_for_review": ans.marked_for_review,
        })
    attempt, before, after = submit_assessment(db, a, user.id, answers)

    strengths, weaknesses = [], []
    for tid_str, after_val in after.items():
        tid = int(tid_str)
        topic = db.query(Topic).filter(Topic.id == tid).first()
        name = topic.name if topic else "Topic"
        change = round(after_val - before.get(tid_str, 0), 1)
        entry = {"topic": name, "mastery": after_val, "change": change}
        (strengths if after_val >= 60 else weaknesses).append(entry)

    return {
        "attempt_id": attempt.id, "score": attempt.score, "correct_count": attempt.correct_count,
        "total_questions": attempt.total_questions, "mastery_before": before, "mastery_after": after,
        "strengths": strengths, "weaknesses": weaknesses,
    }
