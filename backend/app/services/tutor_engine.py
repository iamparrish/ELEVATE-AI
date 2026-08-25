import os
import re
import httpx
from sqlalchemy.orm import Session

from app.models.models import Topic, LearningResource, ChatMessage
from app.services.learner_model import calculate_topic_mastery
from app.services.document_engine import retrieve_relevant_chunks

AI_API_KEY = os.environ.get("AI_API_KEY", "").strip()
AI_MODEL = os.environ.get("AI_MODEL", "claude-sonnet-4-6")


def _guess_topic(db: Session, message: str, subject_hint=None):
    words = set(w.lower() for w in re.findall(r"[a-zA-Z]{3,}", message))
    topics = db.query(Topic).all()
    best, best_score = None, 0
    for t in topics:
        t_words = set(w.lower() for w in re.findall(r"[a-zA-Z]{3,}", t.name))
        score = len(words & t_words)
        if score > best_score:
            best, best_score = t, score
    return best


def _demo_reply(db: Session, student_id: int, message: str, action_type: str, topic: Topic, resource: LearningResource):
    grounded_in = None
    grounded_snippet = ""
    if resource:
        chunks = retrieve_relevant_chunks(resource, message, top_k=2)
        if chunks:
            grounded_in = resource.filename
            grounded_snippet = " ".join(c["text"] for c in chunks)[:500]

    mastery = None
    if topic:
        mastery = calculate_topic_mastery(db, student_id, topic.id)

    topic_name = topic.name if topic else "this concept"

    if action_type == "hint":
        text = f"Here's a hint for {topic_name}: think about what happens first in the process, and what changes as a result. Try to state the relationship in your own words before checking the full explanation."
    elif action_type == "simpler":
        text = f"Let's simplify {topic_name}. Imagine explaining it to a younger student, using only everyday language and a small concrete example, without any formulas or jargon."
    elif action_type == "example":
        text = f"Here's a worked example involving {topic_name}: picture a simple, real-world scenario where this concept directly applies, then walk through it step by step to see the concept in action."
    elif action_type == "summary":
        if grounded_snippet:
            text = f"Summary grounded in {grounded_in}: {grounded_snippet[:280]}..."
        else:
            text = f"Quick summary of {topic_name}: focus on the core definition, why it matters, and the one mistake students most often make with it."
    elif action_type == "practice":
        text = f"Let's practice {topic_name}. I'll generate a short set of questions calibrated to your current level - use the \"Generate Similar Questions\" option on Quiz Practice, or I can start one here if you'd like."
    elif action_type == "quiz":
        text = f"I can generate a personalized quiz on {topic_name} based on your current mastery. Head to Quiz Practice > Topic Practice, or ask me to generate one directly."
    else:
        if grounded_snippet:
            text = (
                f"Based on \"{grounded_in}\": {grounded_snippet[:350]}\n\n"
                f"Before I explain further - what do you already know about {topic_name}? "
                f"Try describing it in one or two sentences and I'll build on that."
            )
        elif topic:
            level_note = ""
            if mastery and mastery["has_data"]:
                if mastery["mastery"] < 40:
                    level_note = " Since this is still developing for you, let's start from the basics."
                elif mastery["mastery"] >= 70:
                    level_note = " Since you're doing well here, let's push into a more advanced angle."
            text = (
                f"Good question about {topic_name}.{level_note} Before I give you the full explanation, "
                f"can you tell me what you already understand about it? That way I can fill in exactly the "
                f"gap rather than repeating what you already know."
            )
        else:
            text = (
                "I want to make sure I ground this in the right concept. Could you tell me which subject "
                "or topic this question relates to, or upload the related study material so I can check it directly?"
            )

    if resource and not grounded_snippet:
        text += f"\n\n(I couldn't find this specific detail in \"{resource.filename}\" - this answer is from general knowledge, not that document.)"

    return text, grounded_in


async def _llm_reply(message: str, context: str):
    """Optional real-LLM path. Only used if AI_API_KEY is set - the app is
    fully functional without it via _demo_reply."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": AI_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": AI_MODEL,
                "max_tokens": 400,
                "system": (
                    "You are the ELEVATE AI Tutor. Guide the student toward understanding rather than "
                    "giving final answers outright. Use the provided context if relevant; if the answer "
                    "isn't in the context, say so rather than inventing a source-based claim."
                ),
                "messages": [{"role": "user", "content": f"Context: {context}\n\nStudent: {message}"}],
            },
        )
        data = resp.json()
        blocks = data.get("content", [])
        return "".join(b.get("text", "") for b in blocks if b.get("type") == "text")


async def get_tutor_reply(db: Session, student_id: int, message: str, action_type: str = None,
                           topic_id: int = None, material_id: int = None):
    topic = db.query(Topic).filter(Topic.id == topic_id).first() if topic_id else _guess_topic(db, message)
    resource = db.query(LearningResource).filter(LearningResource.id == material_id).first() if material_id else None

    if AI_API_KEY:
        context = ""
        if resource:
            chunks = retrieve_relevant_chunks(resource, message, top_k=2)
            context = " ".join(c["text"] for c in chunks)
        try:
            text = await _llm_reply(message, context)
            grounded_in = resource.filename if (resource and context) else None
            return text, grounded_in
        except Exception:
            pass  # fall through to demo mode on any API error

    return _demo_reply(db, student_id, message, action_type or "chat", topic, resource)
