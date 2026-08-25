from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.models import User, ChatSession, ChatMessage
from app.schemas.schemas import TutorChatIn
from app.utils.security import require_student
from app.services.tutor_engine import get_tutor_reply
from app.services.learner_model import log_event

router = APIRouter(prefix="/api/tutor", tags=["tutor"])


@router.get("/sessions")
def list_sessions(user: User = Depends(require_student), db: Session = Depends(get_db)):
    sessions = db.query(ChatSession).filter(ChatSession.student_id == user.id).order_by(ChatSession.created_at.desc()).all()
    return {"sessions": [{"id": s.id, "title": s.title, "created_at": s.created_at.isoformat()} for s in sessions]}


@router.get("/sessions/{session_id}/messages")
def get_messages(session_id: int, user: User = Depends(require_student), db: Session = Depends(get_db)):
    msgs = db.query(ChatMessage).join(ChatSession, ChatMessage.session_id == ChatSession.id).filter(
        ChatSession.id == session_id, ChatSession.student_id == user.id).order_by(ChatMessage.created_at).all()
    return {"messages": [
        {"role": m.role, "content": m.content, "grounded_in": m.grounded_in, "action_type": m.action_type,
         "created_at": m.created_at.isoformat()} for m in msgs
    ]}


@router.post("/chat")
async def chat(body: TutorChatIn, user: User = Depends(require_student), db: Session = Depends(get_db)):
    session = None
    if body.session_id:
        session = db.query(ChatSession).filter(ChatSession.id == body.session_id, ChatSession.student_id == user.id).first()
    if not session:
        session = ChatSession(student_id=user.id, topic_id=body.topic_id, material_id=body.material_id,
                               title=body.message[:40])
        db.add(session)
        db.commit()
        db.refresh(session)

    db.add(ChatMessage(session_id=session.id, role="student", content=body.message, action_type=body.action_type))
    db.commit()

    reply_text, grounded_in = await get_tutor_reply(
        db, user.id, body.message, action_type=body.action_type,
        topic_id=body.topic_id or session.topic_id, material_id=body.material_id or session.material_id,
    )

    msg = ChatMessage(session_id=session.id, role="tutor", content=reply_text, grounded_in=grounded_in,
                       action_type=body.action_type)
    db.add(msg)
    db.commit()

    log_event(db, user.id, "tutor_session", topic_id=body.topic_id or session.topic_id,
              payload={"session_id": session.id}, duration_seconds=20)

    return {
        "session_id": session.id, "reply": reply_text, "grounded_in": grounded_in,
        "actions": ["hint", "simpler", "example", "summarize", "practice", "quiz"],
    }
