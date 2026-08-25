import datetime as dt
from sqlalchemy.orm import Session

from app.models.models import (
    Assessment, AssessmentAttempt, AssessmentAnswer, Question, Topic, Subject,
)
from app.services.learner_model import calculate_topic_mastery, log_event, notify
from app.services.quiz_engine import _pick_from_bank


def build_assessment(db: Session, student_id, assessment_type, subject_id=None, topic_id=None, num_questions=10):
    titles = {
        "diagnostic": "Diagnostic Assessment", "recommended": "Recommended Assessment",
        "topic_test": "Topic Test", "revision_test": "Revision Test", "adaptive": "Adaptive Assessment",
    }
    question_ids = []
    if topic_id:
        pool = _pick_from_bank(db, topic_id, "adaptive" if assessment_type == "adaptive" else "medium", num_questions)
        question_ids = [q.id for q in pool]
    elif subject_id:
        topics = db.query(Topic).filter(Topic.subject_id == subject_id).all()
        per = max(1, num_questions // max(1, len(topics)))
        for t in topics:
            question_ids += [q.id for q in _pick_from_bank(db, t.id, "medium", per)]
        question_ids = question_ids[:num_questions]

    assessment = Assessment(
        title=titles.get(assessment_type, "Assessment"), assessment_type=assessment_type,
        subject_id=subject_id, topic_id=topic_id, student_id=student_id,
        question_ids=question_ids, time_limit_minutes=max(10, num_questions * 2),
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment


def get_assessment_payload(db: Session, assessment: Assessment):
    out = []
    for qid in assessment.question_ids:
        q = db.query(Question).filter(Question.id == qid).first()
        if q:
            out.append({
                "question_id": q.id, "question_text": q.question_text, "options": q.options,
                "difficulty": q.difficulty, "topic_id": q.topic_id,
            })
    return out


def submit_assessment(db: Session, assessment: Assessment, student_id: int, answers: list):
    mastery_before = {}
    topics_involved = set(q_ans.get("topic_id") for q_ans in answers if q_ans.get("topic_id"))
    for t in topics_involved:
        mastery_before[str(t)] = calculate_topic_mastery(db, student_id, t)["mastery"]

    attempt = AssessmentAttempt(
        assessment_id=assessment.id, student_id=student_id, total_questions=len(answers),
        started_at=dt.datetime.utcnow(), status="in_progress",
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    correct_count = 0
    for a in answers:
        q = db.query(Question).filter(Question.id == a["question_id"]).first()
        if not q:
            continue
        is_correct = a.get("selected_index") == q.correct_index
        if is_correct:
            correct_count += 1
        db.add(AssessmentAnswer(
            attempt_id=attempt.id, question_id=q.id, selected_index=a.get("selected_index"),
            is_correct=is_correct, marked_for_review=a.get("marked_for_review", False),
            topic_id=q.topic_id, difficulty=q.difficulty,
        ))

    attempt.correct_count = correct_count
    attempt.score = round(100 * correct_count / max(1, len(answers)), 1)
    attempt.submitted_at = dt.datetime.utcnow()
    attempt.status = "completed"
    attempt.mastery_before = mastery_before
    db.commit()

    for t in topics_involved:
        log_event(db, student_id, "assessment_attempt", topic_id=t,
                  payload={"assessment_id": assessment.id, "attempt_id": attempt.id})

    mastery_after = {}
    for t in topics_involved:
        mastery_after[str(t)] = calculate_topic_mastery(db, student_id, t)["mastery"]
    attempt.mastery_after = mastery_after
    db.commit()

    notify(db, student_id, "assessment_result", f"{assessment.title} results are in",
           f"You scored {attempt.score}%. See your personalized next steps.")

    return attempt, mastery_before, mastery_after
