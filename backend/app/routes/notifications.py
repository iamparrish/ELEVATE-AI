from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.models import User, Notification
from app.utils.security import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("")
def list_notifications(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notifs = db.query(Notification).filter(Notification.user_id == user.id).order_by(Notification.created_at.desc()).limit(30).all()
    return {
        "notifications": [
            {"id": n.id, "type": n.notif_type, "title": n.title, "message": n.message,
             "is_read": n.is_read, "created_at": n.created_at.isoformat()} for n in notifs
        ],
        "unread_count": sum(1 for n in notifs if not n.is_read),
    }


@router.post("/{notif_id}/read")
def mark_read(notif_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    n = db.query(Notification).filter(Notification.id == notif_id, Notification.user_id == user.id).first()
    if n:
        n.is_read = True
        db.commit()
    return {"message": "ok"}
