import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.db import Base, engine
from app.models import models  # noqa - ensures models are registered
from app.routes import auth, student, quizzes, assessments, materials, tutor, knowledge_graph, analytics, teacher, notifications

app = FastAPI(title="ELEVATE AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(student.router)
app.include_router(quizzes.router)
app.include_router(assessments.router)
app.include_router(materials.router)
app.include_router(tutor.router)
app.include_router(knowledge_graph.router)
app.include_router(analytics.router)
app.include_router(teacher.router)
app.include_router(notifications.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "app": "ELEVATE AI"}
