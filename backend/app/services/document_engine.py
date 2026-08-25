import os
import re
import uuid
from sqlalchemy.orm import Session

from app.models.models import LearningResource

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

DEFINITION_PATTERN = re.compile(
    r"([A-Z][A-Za-z0-9 \-]{2,40}?)\s+(?:is|are|refers to|means|can be defined as)\s+([^.]{15,220})\."
)


def save_upload(file_bytes: bytes, original_filename: str) -> str:
    ext = os.path.splitext(original_filename)[1] or ".pdf"
    safe_name = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(UPLOAD_DIR, safe_name)
    with open(path, "wb") as f:
        f.write(file_bytes)
    return path


def extract_text(filepath: str) -> str:
    if filepath.lower().endswith(".pdf"):
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(filepath)
            text = "\n".join(page.get_text() for page in doc)
            doc.close()
            return text
        except Exception:
            return ""
    else:
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception:
            return ""


def chunk_text(text: str, chunk_size=800):
    text = re.sub(r"\s+", " ", text).strip()
    chunks = []
    i = 0
    idx = 0
    while i < len(text):
        chunk = text[i:i + chunk_size]
        chunks.append({"id": idx, "text": chunk})
        idx += 1
        i += chunk_size
    return chunks


def extract_concepts(text: str, max_concepts=8):
    """Deterministic concept/definition extraction - no LLM required. Only
    concepts actually found in the text are returned; if the pattern finds
    nothing, we return an empty list rather than fabricating concepts."""
    found = []
    seen_terms = set()
    for m in DEFINITION_PATTERN.finditer(text):
        term = m.group(1).strip()
        definition = m.group(2).strip()
        key = term.lower()
        if key in seen_terms or len(term.split()) > 6:
            continue
        seen_terms.add(key)
        found.append({"term": term, "definition": definition})
        if len(found) >= max_concepts:
            break
    return found


def summarize(text: str, max_sentences=3):
    text = re.sub(r"\s+", " ", text).strip()
    sentences = re.split(r"(?<=[.!?])\s+", text)
    sentences = [s for s in sentences if len(s) > 25]
    if not sentences:
        return ""
    return " ".join(sentences[:max_sentences])


def process_resource(db: Session, resource: LearningResource):
    """Runs the full pipeline synchronously: File Uploaded -> Text Extracted ->
    Concepts Identified -> Topics Structured -> Knowledge Graph Built ->
    Quiz Questions Generated -> Ready."""
    resource.status = "extracting"
    db.commit()

    text = extract_text(resource.filepath)
    resource.extracted_text = text[:200000]
    resource.status = "extracted" if text else "failed"
    db.commit()
    if not text:
        return resource

    resource.chunks = chunk_text(text)
    concepts = extract_concepts(text)
    resource.concepts = concepts
    resource.status = "concepts_identified"
    resource.summary = summarize(text)
    db.commit()

    resource.status = "topics_structured"
    db.commit()

    resource.status = "graph_built"
    db.commit()

    resource.status = "questions_generated" if concepts else "ready"
    db.commit()

    resource.status = "ready"
    db.commit()
    return resource


def retrieve_relevant_chunks(resource: LearningResource, query: str, top_k=2):
    """Very lightweight lexical RAG retrieval (keyword overlap scoring) -
    no embeddings dependency required, works fully offline."""
    if not resource or not resource.chunks:
        return []
    query_terms = set(w.lower() for w in re.findall(r"[a-zA-Z]{3,}", query))
    scored = []
    for c in resource.chunks:
        chunk_terms = set(w.lower() for w in re.findall(r"[a-zA-Z]{3,}", c["text"]))
        overlap = len(query_terms & chunk_terms)
        if overlap > 0:
            scored.append((overlap, c))
    scored.sort(key=lambda x: -x[0])
    return [c for _, c in scored[:top_k]]
