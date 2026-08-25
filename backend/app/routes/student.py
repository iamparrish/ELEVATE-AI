import datetime as dt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.models import (
    User, StudentProfile, Subject, Topic, LearningUnit, Recommendation, Notification,
    KnowledgeGap, QuizAttempt, AssessmentAttempt, Assessment, LearningEvent,
)
from app.schemas.schemas import OnboardingIn, ProfileUpdateIn
from app.utils.security import require_student
from app.services import learner_model as lm
from app.services.assessment_engine import submit_assessment

router = APIRouter(prefix="/api/student", tags=["student"])


@router.get("/profile")
def get_profile(user: User = Depends(require_student), db: Session = Depends(get_db)):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    return {
        "full_name": user.full_name, "email": user.email, "academic_level": user.academic_level,
        "institution": user.institution, "onboarding_completed": user.onboarding_completed,
        "subjects": profile.subjects if profile else [], "goals": profile.goals if profile else [],
        "preferences": profile.preferences if profile else {},
        "current_streak": profile.current_streak if profile else 0,
        "longest_streak": profile.longest_streak if profile else 0,
    }


@router.put("/profile")
def update_profile(body: ProfileUpdateIn, user: User = Depends(require_student), db: Session = Depends(get_db)):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    if body.full_name:
        user.full_name = body.full_name
    if body.academic_level:
        user.academic_level = body.academic_level
    if body.institution is not None:
        user.institution = body.institution
    if profile:
        if body.subjects is not None:
            profile.subjects = body.subjects
        if body.goals is not None:
            profile.goals = body.goals
        if body.preferences is not None:
            profile.preferences = body.preferences
    db.commit()
    return {"message": "Profile updated"}


@router.post("/onboarding")
def complete_onboarding(body: OnboardingIn, user: User = Depends(require_student), db: Session = Depends(get_db)):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    if not profile:
        profile = StudentProfile(user_id=user.id)
        db.add(profile)

    user.academic_level = body.academic_level
    if body.institution:
        user.institution = body.institution
    profile.subjects = body.subjects
    profile.goals = body.goals
    profile.preferences = body.preferences
    db.commit()

    # Build the student's personalized learning path from chosen subjects' topics.
    order = 0
    for code in body.subjects:
        subject = db.query(Subject).filter(Subject.code == code).first()
        if not subject:
            continue
        topics = db.query(Topic).filter(Topic.subject_id == subject.id).order_by(Topic.order_index).all()
        for t in topics:
            exists = db.query(LearningUnit).filter(LearningUnit.student_id == user.id, LearningUnit.topic_id == t.id).first()
            if not exists:
                db.add(LearningUnit(student_id=user.id, topic_id=t.id, order_index=order))
                order += 1
    db.commit()

    diagnostic_result = None
    if body.diagnostic_answers:
        qids = [a["question_id"] for a in body.diagnostic_answers]
        from app.models.models import Question
        topic_lookup = {q.id: q.topic_id for q in db.query(Question).filter(Question.id.in_(qids)).all()}
        assessment = Assessment(title="Initial Diagnostic Assessment", assessment_type="diagnostic",
                                 student_id=user.id, question_ids=qids, time_limit_minutes=20)
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        answers = []
        for a in body.diagnostic_answers:
            answers.append({
                "question_id": a["question_id"], "selected_index": a.get("selected_index"),
                "topic_id": topic_lookup.get(a["question_id"]),
            })
        attempt, before, after = submit_assessment(db, assessment, user.id, answers)
        diagnostic_result = {"score": attempt.score, "correct": attempt.correct_count, "total": attempt.total_questions}

    profile.diagnostic_completed = bool(body.diagnostic_answers)
    user.onboarding_completed = True
    db.commit()

    lm.recalc_recommendations(db, user.id)
    lm.notify(db, user.id, "recommendation", "Your learning path is ready",
              "ELEVATE AI has built your personalized learning path based on your goals and diagnostic results.")

    return {"message": "Onboarding complete", "diagnostic_result": diagnostic_result}


@router.get("/dashboard")
def dashboard(user: User = Depends(require_student), db: Session = Depends(get_db)):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    progress = lm.overall_progress(db, user.id)
    mastery = lm.overall_mastery(db, user.id)
    units = db.query(LearningUnit).filter(LearningUnit.student_id == user.id).all()

    gaps = db.query(KnowledgeGap).filter(KnowledgeGap.student_id == user.id, KnowledgeGap.status.in_(["gap", "watch"])).all()
    recs = lm.recalc_recommendations(db, user.id)

    recent_events = db.query(LearningEvent).filter(LearningEvent.student_id == user.id).order_by(LearningEvent.created_at.desc()).limit(8).all()
    recent_quizzes = db.query(QuizAttempt).filter(QuizAttempt.student_id == user.id).order_by(QuizAttempt.created_at.desc()).limit(5).all()

    hour = dt.datetime.now().hour
    greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"

    continue_topic = None
    for u in units:
        if u.status in ("in_progress", "developing", "needs_revision"):
            topic = db.query(Topic).filter(Topic.id == u.topic_id).first()
            if topic:
                continue_topic = {"topic_id": topic.id, "topic_name": topic.name, "status": u.status}
                break

    return {
        "greeting": f"{greeting}, {user.full_name.split(' ')[0]}",
        "has_learning_path": len(units) > 0,
        "overall_mastery": mastery if units else None,
        "overall_progress": progress["percent"] if units else None,
        "topics_completed": progress["completed"], "topics_total": progress["total"],
        "current_streak": profile.current_streak if profile else 0,
        "continue_learning": continue_topic,
        "active_knowledge_gaps": len(gaps),
        "recommendations": [
            {"id": r.id, "title": r.title, "reason": r.reason, "type": r.rec_type} for r in recs[:5]
        ],
        "recent_activity": [
            {"type": e.event_type, "at": e.created_at.isoformat()} for e in recent_events
        ],
        "recent_quizzes": [
            {"id": q.id, "accuracy": q.accuracy, "at": q.created_at.isoformat()} for q in recent_quizzes
        ],
    }


@router.get("/progress")
def progress(user: User = Depends(require_student), db: Session = Depends(get_db)):
    prog = lm.overall_progress(db, user.id)
    weekly = lm.weekly_activity(db, user.id)
    return {**prog, "weekly_activity": weekly}


@router.get("/mastery")
def mastery(user: User = Depends(require_student), db: Session = Depends(get_db)):
    units = db.query(LearningUnit).filter(LearningUnit.student_id == user.id).all()
    breakdown = []
    for u in units:
        topic = db.query(Topic).filter(Topic.id == u.topic_id).first()
        stats = lm.calculate_topic_mastery(db, user.id, u.topic_id)
        breakdown.append({"topic_id": u.topic_id, "topic_name": topic.name if topic else "", **stats})
    return {"overall_mastery": lm.overall_mastery(db, user.id), "topics": breakdown}


@router.get("/learning-path")
def learning_path(user: User = Depends(require_student), db: Session = Depends(get_db)):
    units = db.query(LearningUnit).filter(LearningUnit.student_id == user.id).order_by(LearningUnit.order_index).all()
    out = []
    for u in units:
        topic = db.query(Topic).filter(Topic.id == u.topic_id).first()
        subject = db.query(Subject).filter(Subject.id == topic.subject_id).first() if topic else None
        stats = lm.calculate_topic_mastery(db, user.id, u.topic_id)
        out.append({
            "unit_id": u.id, "topic_id": u.topic_id, "topic_name": topic.name if topic else "",
            "subject_name": subject.name if subject else "", "order_index": u.order_index, **stats,
        })
    return {"path": out}


@router.get("/knowledge-gaps")
def knowledge_gaps(user: User = Depends(require_student), db: Session = Depends(get_db)):
    gaps = db.query(KnowledgeGap).filter(KnowledgeGap.student_id == user.id).order_by(KnowledgeGap.updated_at.desc()).all()
    out = []
    for g in gaps:
        topic = db.query(Topic).filter(Topic.id == g.topic_id).first()
        out.append({
            "topic_id": g.topic_id, "topic_name": topic.name if topic else "",
            "mastery": g.mastery_estimate, "trend": g.trend, "status": g.status,
            "common_mistakes": g.common_mistakes, "recommended_actions": g.recommended_actions,
            "updated_at": g.updated_at.isoformat(),
        })
    return {"gaps": out}


@router.get("/recommendations")
def recommendations(user: User = Depends(require_student), db: Session = Depends(get_db)):
    recs = lm.recalc_recommendations(db, user.id)
    out = []
    for r in recs:
        topic = db.query(Topic).filter(Topic.id == r.topic_id).first() if r.topic_id else None
        out.append({"id": r.id, "title": r.title, "reason": r.reason, "type": r.rec_type,
                     "topic_name": topic.name if topic else None, "priority": r.priority})
    return {"recommendations": out}


@router.get("/subjects-catalog")
def subjects_catalog(db: Session = Depends(get_db)):
    subjects = db.query(Subject).all()
    from app.models.models import LearningGoal, LearningPreference
    goals = db.query(LearningGoal).all()
    prefs = db.query(LearningPreference).all()
    return {
        "subjects": [{"code": s.code, "name": s.name, "icon": s.icon, "description": s.description} for s in subjects],
        "goals": [{"code": g.code, "label": g.label} for g in goals],
        "preferences": [{"code": p.code, "label": p.label} for p in prefs],
    }


@router.get("/diagnostic-questions")
def diagnostic_questions(subjects: str, db: Session = Depends(get_db)):
    """Returns a short diagnostic quiz pulled from real bank questions across chosen subjects."""
    from app.models.models import Question
    codes = subjects.split(",") if subjects else []
    out = []
    for code in codes:
        subject = db.query(Subject).filter(Subject.code == code).first()
        if not subject:
            continue
        qs = db.query(Question).filter(Question.subject_id == subject.id, Question.difficulty == "medium").limit(3).all()
        for q in qs:
            out.append({"question_id": q.id, "question_text": q.question_text, "options": q.options, "topic_id": q.topic_id})
    return {"questions": out}
