from sqlalchemy.orm import Session
from app.models.models import (
    User, StudentProfile, LearningUnit, QuizAttempt, AssessmentAttempt, Topic, Recommendation, KnowledgeGap,
)
from app.services.learner_model import overall_mastery, overall_progress, calculate_topic_mastery


def list_students(db: Session):
    students = db.query(User).filter(User.role == "student").all()
    out = []
    for s in students:
        mastery = overall_mastery(db, s.id) or 0.0
        progress = overall_progress(db, s.id)
        gaps = db.query(KnowledgeGap).filter(KnowledgeGap.student_id == s.id, KnowledgeGap.status == "gap").count()
        out.append({
            "id": s.id, "name": s.full_name, "email": s.email,
            "academic_level": s.academic_level, "overall_mastery": mastery,
            "progress_percent": progress["percent"], "active_gaps": gaps,
        })
    return out


def student_detail(db: Session, student_id: int):
    student = db.query(User).filter(User.id == student_id, User.role == "student").first()
    if not student:
        return None
    units = db.query(LearningUnit).filter(LearningUnit.student_id == student_id).all()
    topic_breakdown = []
    for u in units:
        topic = db.query(Topic).filter(Topic.id == u.topic_id).first()
        stats = calculate_topic_mastery(db, student_id, u.topic_id)
        topic_breakdown.append({"topic": topic.name if topic else "Unknown", "topic_id": u.topic_id, **stats})

    quiz_attempts = db.query(QuizAttempt).filter(QuizAttempt.student_id == student_id).order_by(QuizAttempt.created_at.desc()).limit(10).all()
    assessment_attempts = db.query(AssessmentAttempt).filter(AssessmentAttempt.student_id == student_id, AssessmentAttempt.status == "completed").order_by(AssessmentAttempt.submitted_at.desc()).limit(10).all()
    gaps = db.query(KnowledgeGap).filter(KnowledgeGap.student_id == student_id, KnowledgeGap.status == "gap").all()

    return {
        "student": {"id": student.id, "name": student.full_name, "email": student.email,
                    "academic_level": student.academic_level, "institution": student.institution},
        "overall_mastery": overall_mastery(db, student_id) or 0.0,
        "progress": overall_progress(db, student_id),
        "topic_breakdown": topic_breakdown,
        "recent_quizzes": [{"id": a.id, "score": a.score, "accuracy": a.accuracy, "date": a.created_at.isoformat()} for a in quiz_attempts],
        "recent_assessments": [{"id": a.id, "score": a.score, "date": (a.submitted_at or a.started_at).isoformat()} for a in assessment_attempts],
        "weak_areas": [{"topic_id": g.topic_id, "mastery": g.mastery_estimate, "trend": g.trend} for g in gaps],
    }


def class_analytics(db: Session):
    students = db.query(User).filter(User.role == "student").all()
    if not students:
        return {"total_students": 0, "average_mastery": 0.0, "students_needing_support": 0,
                "topic_performance": [], "frequently_misunderstood": []}

    masteries = [overall_mastery(db, s.id) or 0.0 for s in students]
    avg = round(sum(masteries) / len(masteries), 1) if masteries else 0.0
    needing_support = sum(1 for m in masteries if m < 45)

    topics = db.query(Topic).all()
    topic_perf = []
    misunderstood = []
    for t in topics:
        vals = []
        for s in students:
            stats = calculate_topic_mastery(db, s.id, t.id)
            if stats["has_data"]:
                vals.append(stats["mastery"])
        if vals:
            avg_m = round(sum(vals) / len(vals), 1)
            topic_perf.append({"topic": t.name, "average_mastery": avg_m, "students_attempted": len(vals)})
            if avg_m < 50:
                misunderstood.append({"topic": t.name, "average_mastery": avg_m})

    misunderstood.sort(key=lambda x: x["average_mastery"])
    return {
        "total_students": len(students), "average_mastery": avg,
        "students_needing_support": needing_support,
        "topic_performance": topic_perf, "frequently_misunderstood": misunderstood[:5],
    }


def review_recommendation(db: Session, rec_id: int, action: str):
    rec = db.query(Recommendation).filter(Recommendation.id == rec_id).first()
    if not rec:
        return None
    if action == "approve":
        rec.teacher_review_status = "approved"
    elif action == "reject":
        rec.teacher_review_status = "rejected"
        rec.status = "dismissed"
    elif action == "regenerate":
        rec.teacher_review_status = "regenerated"
    db.commit()
    return rec
