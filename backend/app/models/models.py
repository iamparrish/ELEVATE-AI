"""
ELEVATE AI - SQLAlchemy models.
Every table that stores "progress" style data is written as raw events
(learning_events, quiz_answers, assessment_answers) plus derived/cached
snapshots (progress_records, knowledge_gaps) that are recalculated by the
services layer - never hand-set to a fake number.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship
from app.database.db import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)  # 'student' | 'teacher'
    academic_level = Column(String, nullable=True)
    institution = Column(String, nullable=True)
    onboarding_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    student_profile = relationship("StudentProfile", back_populates="user", uselist=False)
    teacher_profile = relationship("TeacherProfile", back_populates="user", uselist=False)


class StudentProfile(Base):
    __tablename__ = "student_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    subjects = Column(JSON, default=list)          # list of subject codes chosen
    goals = Column(JSON, default=list)              # learning goals chosen
    preferences = Column(JSON, default=dict)        # learning preferences (pace, style, etc)
    diagnostic_completed = Column(Boolean, default=False)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_activity_date = Column(String, nullable=True)  # ISO date of last streak-counted activity

    user = relationship("User", back_populates="student_profile")


class TeacherProfile(Base):
    __tablename__ = "teacher_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    department = Column(String, nullable=True)
    subjects_taught = Column(JSON, default=list)

    user = relationship("User", back_populates="teacher_profile")


class Subject(Base):
    __tablename__ = "subjects"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True)
    name = Column(String)
    icon = Column(String, default="book")
    description = Column(String, default="")


class Topic(Base):
    __tablename__ = "topics"
    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    name = Column(String)
    order_index = Column(Integer, default=0)
    difficulty_base = Column(String, default="medium")  # easy/medium/hard baseline
    description = Column(String, default="")
    prerequisites = Column(JSON, default=list)  # list of topic ids


class LearningGoal(Base):
    __tablename__ = "learning_goals"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True)
    label = Column(String)


class LearningPreference(Base):
    __tablename__ = "learning_preferences"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True)
    label = Column(String)


class LearningUnit(Base):
    """A single unit inside a student's personalized learning path (per-topic)."""
    __tablename__ = "learning_units"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    topic_id = Column(Integer, ForeignKey("topics.id"))
    status = Column(String, default="not_started")
    # not_started | in_progress | developing | needs_revision | completed | mastered
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class LearningEvent(Base):
    """Immutable log of every meaningful learning action. Source of truth."""
    __tablename__ = "learning_events"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    event_type = Column(String)
    # quiz_attempt | assessment_attempt | material_opened | material_completed |
    # section_studied | tutor_session | revision_session | topic_completed
    payload = Column(JSON, default=dict)
    duration_seconds = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class StudySession(Base):
    __tablename__ = "study_sessions"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, default=0)
    activity_type = Column(String, default="general")


class Question(Base):
    """Master bank of MCQ-style questions, reusable across quizzes/assessments."""
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"))
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    question_text = Column(Text)
    question_type = Column(String, default="conceptual")
    # conceptual | application | numerical | scenario | assertion_reason | revision
    difficulty = Column(String, default="medium")  # easy | medium | hard
    options = Column(JSON)   # list of 4 strings
    correct_index = Column(Integer)
    explanation = Column(Text)
    option_explanations = Column(JSON, default=list)
    hint = Column(Text, default="")
    source_material_id = Column(Integer, ForeignKey("learning_resources.id"), nullable=True)
    generated_by = Column(String, default="bank")  # bank | demo_ai | llm


class Quiz(Base):
    __tablename__ = "quizzes"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    quiz_mode = Column(String, default="custom")
    # recommended | quick | topic | weak_area | mistakes | daily | custom | material
    difficulty = Column(String, default="medium")  # easy|medium|hard|adaptive
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=True)
    source_material_id = Column(Integer, ForeignKey("learning_resources.id"), nullable=True)
    status = Column(String, default="in_progress")  # in_progress|paused|completed
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    order_index = Column(Integer, default=0)


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))
    student_id = Column(Integer, ForeignKey("users.id"))
    score = Column(Float, nullable=True)
    accuracy = Column(Float, nullable=True)
    total_questions = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    time_taken_seconds = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class QuizAnswer(Base):
    __tablename__ = "quiz_answers"
    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("quiz_attempts.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    selected_index = Column(Integer, nullable=True)
    is_correct = Column(Boolean, default=False)
    response_time_seconds = Column(Integer, default=0)
    difficulty = Column(String, default="medium")
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Assessment(Base):
    __tablename__ = "assessments"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    assessment_type = Column(String, default="topic_test")
    # diagnostic | recommended | topic_test | revision_test | adaptive
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # null = template, else personalized
    question_ids = Column(JSON, default=list)
    time_limit_minutes = Column(Integer, default=20)
    created_at = Column(DateTime, default=datetime.utcnow)


class AssessmentAttempt(Base):
    __tablename__ = "assessment_attempts"
    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"))
    student_id = Column(Integer, ForeignKey("users.id"))
    score = Column(Float, nullable=True)
    total_questions = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    mastery_before = Column(JSON, default=dict)
    mastery_after = Column(JSON, default=dict)
    started_at = Column(DateTime, default=datetime.utcnow)
    submitted_at = Column(DateTime, nullable=True)
    status = Column(String, default="in_progress")


class AssessmentAnswer(Base):
    __tablename__ = "assessment_answers"
    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("assessment_attempts.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    selected_index = Column(Integer, nullable=True)
    is_correct = Column(Boolean, default=False)
    marked_for_review = Column(Boolean, default=False)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    difficulty = Column(String, default="medium")


class LearningResource(Base):
    """Uploaded study material (RAG source)."""
    __tablename__ = "learning_resources"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    filename = Column(String)
    filepath = Column(String)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    status = Column(String, default="uploaded")
    # uploaded | extracting | extracted | concepts_identified | topics_structured |
    # graph_built | questions_generated | ready | failed
    extracted_text = Column(Text, default="")
    chunks = Column(JSON, default=list)   # list of {id, text} for RAG retrieval
    concepts = Column(JSON, default=list)
    summary = Column(Text, default="")
    open_count = Column(Integer, default=0)
    total_seconds_viewed = Column(Integer, default=0)
    progress_percent = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)


class KnowledgeGap(Base):
    __tablename__ = "knowledge_gaps"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    topic_id = Column(Integer, ForeignKey("topics.id"))
    mastery_estimate = Column(Float, default=0.0)
    trend = Column(String, default="stable")  # improving|declining|stable
    status = Column(String, default="gap")     # gap|watch|resolved
    common_mistakes = Column(JSON, default=list)
    recommended_actions = Column(JSON, default=list)
    updated_at = Column(DateTime, default=datetime.utcnow)


class Recommendation(Base):
    __tablename__ = "recommendations"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    rec_type = Column(String, default="practice")  # practice|revision|advance|material|tutor
    title = Column(String)
    reason = Column(String)
    priority = Column(Integer, default=1)
    status = Column(String, default="active")  # active|dismissed|completed
    teacher_review_status = Column(String, default="pending")  # pending|approved|edited|rejected|regenerated
    created_at = Column(DateTime, default=datetime.utcnow)


class ProgressRecord(Base):
    """Cached daily snapshot of derived metrics, recomputed by services (not user-editable)."""
    __tablename__ = "progress_records"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    date = Column(String)  # ISO date
    overall_mastery = Column(Float, default=0.0)
    overall_progress = Column(Float, default=0.0)
    topics_completed = Column(Integer, default=0)
    quizzes_taken = Column(Integer, default=0)
    minutes_studied = Column(Integer, default=0)


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    material_id = Column(Integer, ForeignKey("learning_resources.id"), nullable=True)
    title = Column(String, default="New conversation")
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))
    role = Column(String)  # student | tutor
    content = Column(Text)
    grounded_in = Column(String, nullable=True)
    action_type = Column(String, nullable=True)  # hint|simpler|example|summary|practice|quiz
    created_at = Column(DateTime, default=datetime.utcnow)


class KnowledgeNode(Base):
    __tablename__ = "knowledge_nodes"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    topic_id = Column(Integer, ForeignKey("topics.id"))
    label = Column(String)
    subject = Column(String)
    x = Column(Float, default=0.0)
    y = Column(Float, default=0.0)


class KnowledgeEdge(Base):
    __tablename__ = "knowledge_edges"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    source_topic_id = Column(Integer, ForeignKey("topics.id"))
    target_topic_id = Column(Integer, ForeignKey("topics.id"))
    relation = Column(String, default="prerequisite")  # prerequisite|dependency|related


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    notif_type = Column(String, default="general")
    # assessment_result|recommendation|mastery_change|new_quiz|reminder|general
    title = Column(String)
    message = Column(String)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
