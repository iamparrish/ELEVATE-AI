from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr


class RegisterIn(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    confirm_password: str
    academic_level: Optional[str] = None
    institution: Optional[str] = None
    role: str  # student | teacher


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class OnboardingIn(BaseModel):
    academic_level: str
    institution: Optional[str] = None
    subjects: List[str]
    goals: List[str]
    preferences: Dict[str, Any] = {}
    diagnostic_answers: List[Dict[str, Any]] = []  # [{question_id, selected_index}]


class ProfileUpdateIn(BaseModel):
    full_name: Optional[str] = None
    academic_level: Optional[str] = None
    institution: Optional[str] = None
    subjects: Optional[List[str]] = None
    goals: Optional[List[str]] = None
    preferences: Optional[Dict[str, Any]] = None


class QuizGenerateIn(BaseModel):
    quiz_mode: str
    subject_id: Optional[int] = None
    topic_id: Optional[int] = None
    difficulty: str = "medium"
    num_questions: int = 5
    question_type: Optional[str] = None
    material_id: Optional[int] = None


class QuizAnswerIn(BaseModel):
    question_id: int
    selected_index: Optional[int] = None
    response_time_seconds: int = 0


class QuizSubmitIn(BaseModel):
    answers: List[QuizAnswerIn]
    time_taken_seconds: int = 0


class AssessmentBuildIn(BaseModel):
    assessment_type: str = "topic_test"
    subject_id: Optional[int] = None
    topic_id: Optional[int] = None
    num_questions: int = 10


class AssessmentAnswerIn(BaseModel):
    question_id: int
    selected_index: Optional[int] = None
    topic_id: Optional[int] = None
    marked_for_review: bool = False


class AssessmentSubmitIn(BaseModel):
    answers: List[AssessmentAnswerIn]


class TutorChatIn(BaseModel):
    session_id: Optional[int] = None
    message: str
    action_type: Optional[str] = None
    topic_id: Optional[int] = None
    material_id: Optional[int] = None


class RecommendationReviewIn(BaseModel):
    action: str  # approve | reject | regenerate
