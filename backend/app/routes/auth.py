from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.models import User, StudentProfile, TeacherProfile
from app.schemas.schemas import RegisterIn, LoginIn
from app.utils.security import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register")
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if body.password != body.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    if body.role not in ("student", "teacher"):
        raise HTTPException(status_code=400, detail="Role must be student or teacher")
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    user = User(
        full_name=body.full_name, email=body.email, password_hash=hash_password(body.password),
        role=body.role, academic_level=body.academic_level, institution=body.institution,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    if user.role == "student":
        db.add(StudentProfile(user_id=user.id))
    else:
        db.add(TeacherProfile(user_id=user.id))
    db.commit()

    token = create_access_token(user.id, user.role)
    return {"token": token, "user": _user_out(user)}


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(user.id, user.role)
    return {"token": token, "user": _user_out(user)}


@router.post("/logout")
def logout(user: User = Depends(get_current_user)):
    # JWTs are stateless; the frontend simply discards the token.
    return {"message": "Logged out"}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return _user_out(user)


def _user_out(user: User):
    return {
        "id": user.id, "full_name": user.full_name, "email": user.email, "role": user.role,
        "academic_level": user.academic_level, "institution": user.institution,
        "onboarding_completed": user.onboarding_completed,
    }
