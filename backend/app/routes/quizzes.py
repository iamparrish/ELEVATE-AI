from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.models import User, Quiz, QuizAttempt, QuizQuestion
from app.schemas.schemas import QuizGenerateIn, QuizSubmitIn
from app.utils.security import require_student
from app.services.quiz_engine import generate_quiz, get_quiz_payload, submit_quiz

router = APIRouter(prefix="/api/quizzes", tags=["quizzes"])


@router.get("")
def list_quizzes(user: User = Depends(require_student), db: Session = Depends(get_db)):
    quizzes = db.query(Quiz).filter(Quiz.student_id == user.id).order_by(Quiz.created_at.desc()).limit(20).all()
    out = []
    for q in quizzes:
        attempt = db.query(QuizAttempt).filter(QuizAttempt.quiz_id == q.id).order_by(QuizAttempt.created_at.desc()).first()
        out.append({
            "id": q.id, "title": q.title, "mode": q.quiz_mode, "status": q.status,
            "difficulty": q.difficulty, "created_at": q.created_at.isoformat(),
            "accuracy": attempt.accuracy if attempt else None,
        })
    return {"quizzes": out}


@router.post("/generate")
def generate(body: QuizGenerateIn, user: User = Depends(require_student), db: Session = Depends(get_db)):
    quiz, questions = generate_quiz(
        db, user.id, body.quiz_mode, subject_id=body.subject_id, topic_id=body.topic_id,
        difficulty=body.difficulty, num_questions=body.num_questions,
        question_type=body.question_type, material_id=body.material_id,
    )
    if not questions:
        raise HTTPException(status_code=400, detail="Not enough question bank content for this selection yet. Try a different topic or fewer questions.")
    return {"quiz_id": quiz.id, "title": quiz.title, "questions": get_quiz_payload(db, quiz)}


@router.get("/{quiz_id}")
def get_quiz(quiz_id: int, user: User = Depends(require_student), db: Session = Depends(get_db)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id, Quiz.student_id == user.id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return {"quiz_id": quiz.id, "title": quiz.title, "status": quiz.status, "questions": get_quiz_payload(db, quiz)}


@router.post("/{quiz_id}/submit")
def submit(quiz_id: int, body: QuizSubmitIn, user: User = Depends(require_student), db: Session = Depends(get_db)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id, Quiz.student_id == user.id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    answers = [a.dict() for a in body.answers]
    attempt, topic_results = submit_quiz(db, quiz, user.id, answers, body.time_taken_seconds)
    return {
        "attempt_id": attempt.id, "score": attempt.score, "accuracy": attempt.accuracy,
        "correct_count": attempt.correct_count, "total_questions": attempt.total_questions,
        "topic_results": {str(k): v for k, v in topic_results.items()},
    }


@router.post("/{quiz_id}/retry")
def retry_incorrect(quiz_id: int, user: User = Depends(require_student), db: Session = Depends(get_db)):
    from app.models.models import QuizAnswer, QuizAttempt as QA, QuizQuestion
    attempt = db.query(QA).filter(QA.quiz_id == quiz_id, QA.student_id == user.id).order_by(QA.created_at.desc()).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="No attempt found for this quiz")
    wrong = db.query(QuizAnswer).filter(QuizAnswer.attempt_id == attempt.id, QuizAnswer.is_correct == False).all()  # noqa: E712
    if not wrong:
        return {"message": "No incorrect questions to retry - great job!", "quiz_id": None}

    orig = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    new_quiz = Quiz(
        student_id=user.id, title=f"Retry: {orig.title}", quiz_mode="mistakes",
        difficulty=orig.difficulty, topic_id=orig.topic_id, subject_id=orig.subject_id,
    )
    db.add(new_quiz)
    db.commit()
    db.refresh(new_quiz)
    for i, w in enumerate(wrong):
        db.add(QuizQuestion(quiz_id=new_quiz.id, question_id=w.question_id, order_index=i))
    db.commit()
    return {"quiz_id": new_quiz.id, "message": f"Retry quiz created with {len(wrong)} question(s)."}
