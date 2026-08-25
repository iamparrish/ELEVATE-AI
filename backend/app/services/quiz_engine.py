import random
import datetime as dt
from sqlalchemy.orm import Session

from app.models.models import (
    Question, Quiz, QuizQuestion, QuizAttempt, QuizAnswer, Topic, LearningResource,
)
from app.services.learner_model import calculate_topic_mastery, log_event, notify

DIFFICULTY_ORDER = ["easy", "medium", "hard"]


def _pick_from_bank(db: Session, topic_id: int, difficulty: str, n: int, exclude_ids=None):
    exclude_ids = exclude_ids or []
    q = db.query(Question).filter(Question.topic_id == topic_id)
    if difficulty != "adaptive":
        q = q.filter(Question.difficulty == difficulty)
    if exclude_ids:
        q = q.filter(~Question.id.in_(exclude_ids))
    pool = q.all()
    random.shuffle(pool)
    if len(pool) < n and difficulty != "adaptive":
        # top up with other difficulties rather than fail
        more = db.query(Question).filter(Question.topic_id == topic_id, ~Question.id.in_([p.id for p in pool])).all()
        random.shuffle(more)
        pool += more
    return pool[:n]


def _material_grounded_questions(db: Session, resource: LearningResource, n: int):
    """Builds simple, source-grounded MCQs directly from a resource's extracted
    concepts/chunks. No hallucination: every stem is built from actual
    extracted text, and if there isn't enough content, fewer questions are
    returned rather than inventing content."""
    concepts = resource.concepts or []
    out = []
    for c in concepts[:n]:
        term = c.get("term", "").strip()
        definition = c.get("definition", "").strip()
        if not term or not definition:
            continue
        distractors = [x.get("definition", "") for x in concepts if x.get("term") != term][:3]
        while len(distractors) < 3:
            distractors.append("None of the concepts covered in this material apply here.")
        options = distractors[:3] + [definition]
        random.shuffle(options)
        correct_index = options.index(definition)
        out.append({
            "question_text": f"According to \"{resource.filename}\", what best describes \"{term}\"?",
            "options": options,
            "correct_index": correct_index,
            "explanation": f"The material defines {term} as: {definition}",
            "difficulty": "medium",
            "question_type": "conceptual",
            "hint": f"Look at how the material introduces \"{term}\".",
            "grounded_in": resource.filename,
        })
    return out


def generate_quiz(db: Session, student_id: int, quiz_mode: str, subject_id=None, topic_id=None,
                   difficulty="medium", num_questions=5, question_type=None, material_id=None):
    title_map = {
        "recommended": "Recommended For You", "quick": "Quick Practice", "topic": "Topic Practice",
        "weak_area": "Weak Area Practice", "mistakes": "Previous Mistakes", "daily": "Daily Quiz",
        "custom": "Custom Quiz", "material": "Quiz From Study Material",
    }
    quiz = Quiz(student_id=student_id, title=title_map.get(quiz_mode, "Quiz"), quiz_mode=quiz_mode,
                difficulty=difficulty, topic_id=topic_id, subject_id=subject_id, source_material_id=material_id)
    db.add(quiz)
    db.commit()
    db.refresh(quiz)

    questions = []

    if quiz_mode == "material" and material_id:
        resource = db.query(LearningResource).filter(LearningResource.id == material_id).first()
        if resource:
            generated = _material_grounded_questions(db, resource, num_questions)
            for g in generated:
                dbq = Question(
                    topic_id=resource.topic_id, subject_id=resource.subject_id,
                    question_text=g["question_text"], question_type=g["question_type"],
                    difficulty=g["difficulty"], options=g["options"], correct_index=g["correct_index"],
                    explanation=g["explanation"], hint=g["hint"], source_material_id=resource.id,
                    generated_by="demo_ai",
                )
                db.add(dbq)
                db.commit()
                db.refresh(dbq)
                questions.append(dbq)

    elif quiz_mode == "mistakes":
        wrong_qids = (
            db.query(QuizAnswer.question_id)
            .join(QuizAttempt, QuizAnswer.attempt_id == QuizAttempt.id)
            .filter(QuizAttempt.student_id == student_id, QuizAnswer.is_correct == False)  # noqa: E712
            .distinct()
            .all()
        )
        ids = [q[0] for q in wrong_qids]
        pool = db.query(Question).filter(Question.id.in_(ids)).all()
        random.shuffle(pool)
        questions = pool[:num_questions]

    elif quiz_mode in ("weak_area", "daily", "recommended"):
        from app.models.models import KnowledgeGap, LearningUnit
        gap_topics = [g.topic_id for g in db.query(KnowledgeGap).filter(
            KnowledgeGap.student_id == student_id, KnowledgeGap.status.in_(["gap", "watch"])).all()]
        if not gap_topics:
            units = db.query(LearningUnit).filter(LearningUnit.student_id == student_id).all()
            gap_topics = [u.topic_id for u in units][:3]
        remaining = num_questions
        for t in gap_topics:
            if remaining <= 0:
                break
            picked = _pick_from_bank(db, t, "easy" if quiz_mode == "weak_area" else "medium",
                                      min(remaining, 3))
            questions += picked
            remaining -= len(picked)
        if len(questions) < num_questions and topic_id:
            questions += _pick_from_bank(db, topic_id, difficulty, num_questions - len(questions))

    else:  # quick, topic, custom
        if topic_id:
            questions = _pick_from_bank(db, topic_id, difficulty, num_questions)
        elif subject_id:
            topics = db.query(Topic).filter(Topic.subject_id == subject_id).all()
            per = max(1, num_questions // max(1, len(topics)))
            for t in topics:
                questions += _pick_from_bank(db, t.id, difficulty, per)
            questions = questions[:num_questions]

    for i, q in enumerate(questions):
        db.add(QuizQuestion(quiz_id=quiz.id, question_id=q.id, order_index=i))
    db.commit()

    return quiz, questions


def get_quiz_payload(db: Session, quiz: Quiz):
    qq = db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz.id).order_by(QuizQuestion.order_index).all()
    out = []
    for item in qq:
        q = db.query(Question).filter(Question.id == item.question_id).first()
        if not q:
            continue
        out.append({
            "question_id": q.id, "question_text": q.question_text, "options": q.options,
            "difficulty": q.difficulty, "question_type": q.question_type, "hint": q.hint,
            "topic_id": q.topic_id, "grounded_in": None if not q.source_material_id else _resource_name(db, q.source_material_id),
        })
    return out


def _resource_name(db, resource_id):
    r = db.query(LearningResource).filter(LearningResource.id == resource_id).first()
    return r.filename if r else None


def submit_quiz(db: Session, quiz: Quiz, student_id: int, answers: list, time_taken_seconds: int):
    """answers: list of {question_id, selected_index, response_time_seconds}"""
    attempt = QuizAttempt(quiz_id=quiz.id, student_id=student_id, total_questions=len(answers),
                           time_taken_seconds=time_taken_seconds)
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    correct_count = 0
    topic_results = {}
    for a in answers:
        q = db.query(Question).filter(Question.id == a["question_id"]).first()
        if not q:
            continue
        is_correct = a.get("selected_index") == q.correct_index
        if is_correct:
            correct_count += 1
        db.add(QuizAnswer(
            attempt_id=attempt.id, question_id=q.id, selected_index=a.get("selected_index"),
            is_correct=is_correct, response_time_seconds=a.get("response_time_seconds", 0),
            difficulty=q.difficulty, topic_id=q.topic_id,
        ))
        topic_results.setdefault(q.topic_id, {"correct": 0, "total": 0})
        topic_results[q.topic_id]["total"] += 1
        if is_correct:
            topic_results[q.topic_id]["correct"] += 1

    attempt.correct_count = correct_count
    attempt.accuracy = round(100 * correct_count / max(1, len(answers)), 1)
    attempt.score = attempt.accuracy
    quiz.status = "completed"
    quiz.completed_at = dt.datetime.utcnow()
    db.commit()

    for topic_id in topic_results:
        log_event(db, student_id, "quiz_attempt", topic_id=topic_id,
                  payload={"quiz_id": quiz.id, "attempt_id": attempt.id})

    if attempt.accuracy is not None and attempt.accuracy < 50:
        notify(db, student_id, "mastery_change", "Some topics need attention",
               f"Your recent quiz accuracy was {attempt.accuracy}%. Check Knowledge Gaps for targeted practice.")
    else:
        notify(db, student_id, "assessment_result", "Quiz completed",
               f"You scored {attempt.accuracy}% on \"{quiz.title}\".")

    return attempt, topic_results


def adaptive_next_difficulty(recent_correct_streak: int, recent_wrong_streak: int, current: str):
    idx = DIFFICULTY_ORDER.index(current) if current in DIFFICULTY_ORDER else 1
    if recent_correct_streak >= 2:
        idx = min(idx + 1, len(DIFFICULTY_ORDER) - 1)
    elif recent_wrong_streak >= 2:
        idx = max(idx - 1, 0)
    return DIFFICULTY_ORDER[idx]
