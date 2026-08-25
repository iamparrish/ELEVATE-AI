from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.models import User, LearningResource, Subject, Topic
from app.utils.security import require_student
from app.services.document_engine import save_upload, process_resource
from app.services.learner_model import log_event

router = APIRouter(prefix="/api/materials", tags=["materials"])

ALLOWED_EXT = (".pdf", ".txt", ".md")


@router.post("/upload")
async def upload(
    file: UploadFile = File(...),
    subject_id: int = Form(None),
    topic_id: int = Form(None),
    user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    if not file.filename.lower().endswith(ALLOWED_EXT):
        raise HTTPException(status_code=400, detail="Only PDF or text-based files are supported")
    content = await file.read()
    path = save_upload(content, file.filename)

    resource = LearningResource(
        student_id=user.id, filename=file.filename, filepath=path,
        subject_id=subject_id, topic_id=topic_id, status="uploaded",
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)

    process_resource(db, resource)

    if topic_id:
        log_event(db, user.id, "material_opened", topic_id=topic_id, payload={"resource_id": resource.id})

    return _resource_out(resource)


@router.get("")
def list_materials(user: User = Depends(require_student), db: Session = Depends(get_db)):
    resources = db.query(LearningResource).filter(LearningResource.student_id == user.id).order_by(LearningResource.created_at.desc()).all()
    return {"materials": [_resource_out(r) for r in resources]}


@router.get("/{material_id}")
def get_material(material_id: int, user: User = Depends(require_student), db: Session = Depends(get_db)):
    r = db.query(LearningResource).filter(LearningResource.id == material_id, LearningResource.student_id == user.id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Material not found")
    r.open_count += 1
    db.commit()
    return _resource_out(r, include_content=True)


@router.post("/{material_id}/mark-viewed")
def mark_viewed(material_id: int, seconds: int = 30, user: User = Depends(require_student), db: Session = Depends(get_db)):
    r = db.query(LearningResource).filter(LearningResource.id == material_id, LearningResource.student_id == user.id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Material not found")
    r.total_seconds_viewed += seconds
    # Meaningful interaction, not instant completion: progress grows with
    # actual time spent, capped until a study/quiz activity confirms mastery.
    r.progress_percent = min(100.0, (r.total_seconds_viewed / 300.0) * 100)
    if r.progress_percent >= 90 and r.topic_id:
        log_event(db, user.id, "material_completed", topic_id=r.topic_id, payload={"resource_id": r.id})
    db.commit()
    return {"progress_percent": r.progress_percent}


@router.get("/{material_id}/knowledge-graph")
def material_graph(material_id: int, user: User = Depends(require_student), db: Session = Depends(get_db)):
    r = db.query(LearningResource).filter(LearningResource.id == material_id, LearningResource.student_id == user.id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Material not found")
    nodes = [{"id": i, "label": c["term"], "description": c["definition"]} for i, c in enumerate(r.concepts or [])]
    edges = [{"source": i, "target": i + 1, "relation": "related"} for i in range(len(nodes) - 1)]
    return {"nodes": nodes, "edges": edges}


def _resource_out(r: LearningResource, include_content=False):
    out = {
        "id": r.id, "filename": r.filename, "status": r.status, "subject_id": r.subject_id,
        "topic_id": r.topic_id, "concepts_count": len(r.concepts or []), "summary": r.summary,
        "progress_percent": r.progress_percent, "open_count": r.open_count,
        "created_at": r.created_at.isoformat(),
    }
    if include_content:
        out["concepts"] = r.concepts
    return out
