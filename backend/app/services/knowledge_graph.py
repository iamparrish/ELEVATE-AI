from sqlalchemy.orm import Session
from app.models.models import LearningUnit, Topic, Subject
from app.services.learner_model import calculate_topic_mastery


def build_graph(db: Session, student_id: int, subject_id: int = None):
    units = db.query(LearningUnit).filter(LearningUnit.student_id == student_id).all()
    topic_ids = [u.topic_id for u in units]
    topics = db.query(Topic).filter(Topic.id.in_(topic_ids)).all()
    if subject_id:
        topics = [t for t in topics if t.subject_id == subject_id]

    nodes = []
    for t in topics:
        stats = calculate_topic_mastery(db, student_id, t.id)
        subject = db.query(Subject).filter(Subject.id == t.subject_id).first()
        nodes.append({
            "id": t.id, "label": t.name, "subject": subject.name if subject else "",
            "mastery": stats["mastery"], "status": stats["status"], "description": t.description,
        })

    edges = []
    topic_id_set = {t.id for t in topics}
    for t in topics:
        for prereq_id in (t.prerequisites or []):
            if prereq_id in topic_id_set:
                edges.append({"source": prereq_id, "target": t.id, "relation": "prerequisite"})

    return {"nodes": nodes, "edges": edges}


def node_detail(db: Session, student_id: int, topic_id: int):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        return None
    stats = calculate_topic_mastery(db, student_id, topic_id)
    prereqs = db.query(Topic).filter(Topic.id.in_(topic.prerequisites or [])).all()
    related = db.query(Topic).filter(Topic.subject_id == topic.subject_id, Topic.id != topic.id).limit(4).all()

    from app.services.learner_model import _common_mistakes, _recommended_actions
    mistakes = _common_mistakes(db, student_id, topic_id)
    actions = _recommended_actions(stats)

    return {
        "topic": topic.name, "description": topic.description, **stats,
        "prerequisites": [p.name for p in prereqs],
        "related_concepts": [r.name for r in related],
        "common_mistakes": mistakes, "recommended_actions": actions,
    }
