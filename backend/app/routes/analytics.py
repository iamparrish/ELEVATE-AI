from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.models import User, QuizAttempt, AssessmentAttempt, LearningUnit, Topic
from app.utils.security import require_student
from app.services import learner_model as lm

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("")
def analytics(user: User = Depends(require_student), db: Session = Depends(get_db)):
    units = db.query(LearningUnit).filter(LearningUnit.student_id == user.id).all()
    if not units:
        return {"has_data": False, "message": "Keep learning to unlock your progress insights."}

    progress = lm.overall_progress(db, user.id)
    mastery = lm.overall_mastery(db, user.id)
    weekly = lm.weekly_activity(db, user.id)

    quiz_attempts = db.query(QuizAttempt).filter(QuizAttempt.student_id == user.id).order_by(QuizAttempt.created_at).all()
    quiz_accuracy_trend = [{"attempt": i + 1, "accuracy": a.accuracy, "date": a.created_at.isoformat()} for i, a in enumerate(quiz_attempts)]

    assessment_attempts = db.query(AssessmentAttempt).filter(AssessmentAttempt.student_id == user.id, AssessmentAttempt.status == "completed").order_by(AssessmentAttempt.submitted_at).all()
    assessment_trend = [{"attempt": i + 1, "score": a.score, "date": (a.submitted_at or a.started_at).isoformat()} for i, a in enumerate(assessment_attempts)]

    topic_mastery = []
    for u in units:
        topic = db.query(Topic).filter(Topic.id == u.topic_id).first()
        stats = lm.calculate_topic_mastery(db, user.id, u.topic_id)
        if stats["has_data"]:
            topic_mastery.append({"topic": topic.name if topic else "", **stats})

    improvement = None
    if len(quiz_attempts) >= 2:
        first_half = quiz_attempts[:len(quiz_attempts) // 2] or [quiz_attempts[0]]
        second_half = quiz_attempts[len(quiz_attempts) // 2:]
        a1 = sum(a.accuracy or 0 for a in first_half) / len(first_half)
        a2 = sum(a.accuracy or 0 for a in second_half) / len(second_half)
        improvement = round(a2 - a1, 1)

    gaps = [t for t in topic_mastery if t["status"] == "needs_revision"]

    return {
        "has_data": True,
        "overall_progress": progress["percent"], "overall_mastery": mastery,
        "weekly_activity": weekly,
        "quiz_accuracy_trend": quiz_accuracy_trend,
        "assessment_trend": assessment_trend,
        "topic_mastery": topic_mastery,
        "weak_areas": gaps,
        "improvement_vs_earlier": improvement,
        "total_quizzes": len(quiz_attempts), "total_assessments": len(assessment_attempts),
    }
