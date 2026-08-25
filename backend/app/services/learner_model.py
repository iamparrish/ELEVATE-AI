"""
The single source of truth for every number shown to a student or teacher.
Nothing here is hard-coded: every value is derived from LearningEvent,
QuizAnswer, AssessmentAnswer and LearningResource rows actually stored in
the database. If there is no data, we return 0 / None / "not_enough_data"
rather than inventing a number.
"""
import datetime as dt
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.models import (
    User, StudentProfile, Topic, Subject, LearningUnit, LearningEvent,
    QuizAttempt, QuizAnswer, AssessmentAttempt, AssessmentAnswer,
    LearningResource, KnowledgeGap, Recommendation, ProgressRecord, Notification,
)

DIFFICULTY_WEIGHT = {"easy": 0.8, "medium": 1.0, "hard": 1.3, "adaptive": 1.1}


def _weighted_answer_records(db: Session, student_id: int, topic_id: int):
    """Collect every answer (quiz + assessment) for a topic, oldest -> newest."""
    records = []

    quiz_rows = (
        db.query(QuizAnswer, QuizAttempt.created_at)
        .join(QuizAttempt, QuizAnswer.attempt_id == QuizAttempt.id)
        .filter(QuizAttempt.student_id == student_id, QuizAnswer.topic_id == topic_id)
        .all()
    )
    for ans, created_at in quiz_rows:
        records.append({
            "correct": bool(ans.is_correct),
            "difficulty": ans.difficulty or "medium",
            "at": created_at or dt.datetime.utcnow(),
        })

    assess_rows = (
        db.query(AssessmentAnswer, AssessmentAttempt.submitted_at, AssessmentAttempt.started_at)
        .join(AssessmentAttempt, AssessmentAnswer.attempt_id == AssessmentAttempt.id)
        .filter(AssessmentAttempt.student_id == student_id, AssessmentAnswer.topic_id == topic_id,
                AssessmentAttempt.status == "completed")
        .all()
    )
    for ans, submitted_at, started_at in assess_rows:
        records.append({
            "correct": bool(ans.is_correct),
            "difficulty": ans.difficulty or "medium",
            "at": submitted_at or started_at or dt.datetime.utcnow(),
        })

    records.sort(key=lambda r: r["at"])
    return records


def calculate_topic_mastery(db: Session, student_id: int, topic_id: int) -> dict:
    """Returns dict: mastery(0-100), status, trend, attempts, accuracy, has_data."""
    records = _weighted_answer_records(db, student_id, topic_id)

    material_events = (
        db.query(LearningEvent)
        .filter(LearningEvent.student_id == student_id, LearningEvent.topic_id == topic_id,
                LearningEvent.event_type.in_(["material_completed", "section_studied"]))
        .count()
    )

    if not records:
        if material_events > 0:
            # Exposure to material only - small, capped contribution. Opening
            # a page never counts as mastery on its own.
            return {"mastery": min(10.0, material_events * 3.0), "status": "in_progress",
                    "trend": "stable", "attempts": 0, "accuracy": None, "has_data": True}
        return {"mastery": 0.0, "status": "not_started", "trend": "stable",
                "attempts": 0, "accuracy": None, "has_data": False}

    n = len(records)
    # Recency weighting: most recent answers count more (exponential decay over order).
    total_w, correct_w = 0.0, 0.0
    for i, r in enumerate(records):
        recency_w = 0.6 + 0.4 * ((i + 1) / n)   # ranges 0.6 -> 1.0
        diff_w = DIFFICULTY_WEIGHT.get(r["difficulty"], 1.0)
        w = recency_w * diff_w
        total_w += w
        if r["correct"]:
            correct_w += w

    accuracy = correct_w / total_w if total_w else 0.0
    # Confidence penalty for very small sample sizes - avoid a single
    # lucky/unlucky answer producing an extreme mastery value.
    confidence = min(1.0, n / 6.0)
    mastery = accuracy * 100 * (0.55 + 0.45 * confidence)

    # Trend: compare last third vs earlier records
    if n >= 4:
        split = max(1, n // 3)
        recent = records[-split:]
        earlier = records[:-split]
        recent_acc = sum(1 for r in recent if r["correct"]) / len(recent)
        earlier_acc = sum(1 for r in earlier if r["correct"]) / len(earlier) if earlier else recent_acc
        if recent_acc - earlier_acc > 0.12:
            trend = "improving"
        elif earlier_acc - recent_acc > 0.12:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "stable"

    material_done = (
        db.query(LearningResource)
        .filter(LearningResource.student_id == student_id, LearningResource.topic_id == topic_id,
                LearningResource.progress_percent >= 90)
        .count() > 0
    ) or material_events >= 2

    recent_wrong_streak = 0
    for r in reversed(records):
        if not r["correct"]:
            recent_wrong_streak += 1
        else:
            break

    if recent_wrong_streak >= 3 or (trend == "declining" and mastery < 55):
        status = "needs_revision"
    elif mastery >= 85 and n >= 5 and trend != "declining":
        status = "mastered"
    elif mastery >= 65 and material_done:
        status = "completed"
    elif mastery >= 40:
        status = "developing"
    else:
        status = "in_progress"

    return {
        "mastery": round(mastery, 1), "status": status, "trend": trend,
        "attempts": n, "accuracy": round(accuracy * 100, 1), "has_data": True,
    }


def recalc_topic_state(db: Session, student_id: int, topic_id: int):
    stats = calculate_topic_mastery(db, student_id, topic_id)

    unit = (
        db.query(LearningUnit)
        .filter(LearningUnit.student_id == student_id, LearningUnit.topic_id == topic_id)
        .first()
    )
    if unit:
        unit.status = stats["status"]

    gap = (
        db.query(KnowledgeGap)
        .filter(KnowledgeGap.student_id == student_id, KnowledgeGap.topic_id == topic_id)
        .first()
    )
    is_gap = stats["status"] == "needs_revision" or (stats["has_data"] and stats["mastery"] < 45)
    if is_gap:
        mistakes = _common_mistakes(db, student_id, topic_id)
        actions = _recommended_actions(stats)
        if not gap:
            gap = KnowledgeGap(student_id=student_id, topic_id=topic_id)
            db.add(gap)
        gap.mastery_estimate = stats["mastery"]
        gap.trend = stats["trend"]
        gap.status = "gap" if stats["mastery"] < 45 else "watch"
        gap.common_mistakes = mistakes
        gap.recommended_actions = actions
        gap.updated_at = dt.datetime.utcnow()
    elif gap:
        gap.status = "resolved"
        gap.mastery_estimate = stats["mastery"]
        gap.trend = stats["trend"]
        gap.updated_at = dt.datetime.utcnow()

    db.commit()
    return stats


def _common_mistakes(db: Session, student_id: int, topic_id: int, limit=3):
    wrong = (
        db.query(QuizAnswer)
        .join(QuizAttempt, QuizAnswer.attempt_id == QuizAttempt.id)
        .filter(QuizAttempt.student_id == student_id, QuizAnswer.topic_id == topic_id,
                QuizAnswer.is_correct == False)  # noqa: E712
        .order_by(QuizAnswer.created_at.desc())
        .limit(limit)
        .all()
    )
    from app.models.models import Question
    out = []
    for w in wrong:
        q = db.query(Question).filter(Question.id == w.question_id).first()
        if q:
            out.append(q.question_text[:120])
    return out


def _recommended_actions(stats):
    actions = []
    if stats["mastery"] < 30:
        actions.append("Review foundational concept explanation with AI Tutor")
        actions.append("Practice 5 easy questions before moving on")
    elif stats["mastery"] < 60:
        actions.append("Retry previously incorrect questions")
        actions.append("Ask AI Tutor for a simpler explanation")
    else:
        actions.append("Attempt harder application-based questions")
    return actions


def get_student_topics(db: Session, student_id: int):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == student_id).first()
    units = db.query(LearningUnit).filter(LearningUnit.student_id == student_id).order_by(LearningUnit.order_index).all()
    return profile, units


def overall_progress(db: Session, student_id: int):
    units = db.query(LearningUnit).filter(LearningUnit.student_id == student_id).all()
    if not units:
        return {"percent": 0.0, "completed": 0, "total": 0}
    done_states = {"completed", "mastered"}
    completed = sum(1 for u in units if u.status in done_states)
    return {"percent": round(100 * completed / len(units), 1), "completed": completed, "total": len(units)}


def overall_mastery(db: Session, student_id: int):
    units = db.query(LearningUnit).filter(LearningUnit.student_id == student_id).all()
    if not units:
        return None
    total = 0.0
    scored = 0
    for u in units:
        stats = calculate_topic_mastery(db, student_id, u.topic_id)
        if stats["has_data"]:
            total += stats["mastery"]
            scored += 1
    if scored == 0:
        return 0.0
    # Un-started topics count as 0 toward the overall average (a student
    # with 8 topics and 2 mastered is not "90% overall" just because the
    # 2 they tried went well).
    return round(total / len(units), 1)


def update_streak(db: Session, student_id: int):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == student_id).first()
    if not profile:
        return
    today = dt.date.today().isoformat()
    if profile.last_activity_date == today:
        return  # already counted today
    yesterday = (dt.date.today() - dt.timedelta(days=1)).isoformat()
    if profile.last_activity_date == yesterday:
        profile.current_streak += 1
    else:
        profile.current_streak = 1
    profile.longest_streak = max(profile.longest_streak, profile.current_streak)
    profile.last_activity_date = today
    db.commit()


def log_event(db: Session, student_id: int, event_type: str, topic_id=None, payload=None, duration_seconds=0,
              counts_for_streak=True):
    ev = LearningEvent(
        student_id=student_id, event_type=event_type, topic_id=topic_id,
        payload=payload or {}, duration_seconds=duration_seconds,
    )
    db.add(ev)
    db.commit()
    if counts_for_streak and event_type in (
        "quiz_attempt", "assessment_attempt", "material_completed", "section_studied",
        "revision_session", "topic_completed", "tutor_session",
    ):
        update_streak(db, student_id)
    if topic_id:
        recalc_topic_state(db, student_id, topic_id)
    snapshot_progress(db, student_id)
    return ev


def snapshot_progress(db: Session, student_id: int):
    today = dt.date.today().isoformat()
    prog = overall_progress(db, student_id)
    mastery = overall_mastery(db, student_id) or 0.0
    topics_completed = prog["completed"]
    quizzes_taken = db.query(QuizAttempt).filter(QuizAttempt.student_id == student_id).count()
    minutes = db.query(func.coalesce(func.sum(LearningEvent.duration_seconds), 0)).filter(
        LearningEvent.student_id == student_id).scalar() or 0

    rec = db.query(ProgressRecord).filter(ProgressRecord.student_id == student_id, ProgressRecord.date == today).first()
    if not rec:
        rec = ProgressRecord(student_id=student_id, date=today)
        db.add(rec)
    rec.overall_mastery = mastery
    rec.overall_progress = prog["percent"]
    rec.topics_completed = topics_completed
    rec.quizzes_taken = quizzes_taken
    rec.minutes_studied = round(minutes / 60)
    db.commit()


def weekly_activity(db: Session, student_id: int, days=7):
    out = []
    today = dt.date.today()
    for i in range(days - 1, -1, -1):
        d = (today - dt.timedelta(days=i)).isoformat()
        count = db.query(LearningEvent).filter(
            LearningEvent.student_id == student_id,
            func.date(LearningEvent.created_at) == d,
        ).count()
        out.append({"date": d, "activity_count": count})
    return out


def recalc_recommendations(db: Session, student_id: int):
    units = db.query(LearningUnit).filter(LearningUnit.student_id == student_id).all()
    active = db.query(Recommendation).filter(Recommendation.student_id == student_id, Recommendation.status == "active").all()
    existing_topic_ids = {r.topic_id for r in active}

    new_recs = []
    for u in units:
        stats = calculate_topic_mastery(db, student_id, u.topic_id)
        topic = db.query(Topic).filter(Topic.id == u.topic_id).first()
        if not topic:
            continue
        if stats["status"] == "needs_revision" and u.topic_id not in existing_topic_ids:
            new_recs.append(Recommendation(
                student_id=student_id, topic_id=u.topic_id, rec_type="revision",
                title=f"Revise {topic.name}",
                reason=f"Recent accuracy suggests a knowledge gap in {topic.name}.",
                priority=3,
            ))
        elif stats["status"] in ("mastered",) and u.topic_id not in existing_topic_ids:
            pass  # no action needed once mastered
        elif stats["has_data"] and stats["mastery"] >= 70 and u.topic_id not in existing_topic_ids:
            new_recs.append(Recommendation(
                student_id=student_id, topic_id=u.topic_id, rec_type="advance",
                title=f"Try advanced practice: {topic.name}",
                reason="Strong recent performance - ready for harder application questions.",
                priority=1,
            ))
        elif not stats["has_data"] and u.topic_id not in existing_topic_ids:
            new_recs.append(Recommendation(
                student_id=student_id, topic_id=u.topic_id, rec_type="practice",
                title=f"Start {topic.name}",
                reason="Not started yet in your personalized path.",
                priority=2,
            ))
    for r in new_recs:
        db.add(r)
    db.commit()
    return db.query(Recommendation).filter(Recommendation.student_id == student_id, Recommendation.status == "active").order_by(Recommendation.priority.desc()).all()


def notify(db: Session, user_id: int, notif_type: str, title: str, message: str):
    n = Notification(user_id=user_id, notif_type=notif_type, title=title, message=message)
    db.add(n)
    db.commit()
    return n
