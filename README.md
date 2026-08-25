# ELEVATE AI — Learn Your Way. At Your Pace. With the Power of AI.

An AI-powered, personalized learning platform built around a continuous adaptive loop:

**ASSESS → ANALYZE → DETECT KNOWLEDGE GAPS → UPDATE LEARNER PROFILE → PERSONALIZE → LEARN → GENERATE MCQs/QUIZZES → PRACTICE → ADAPT DIFFICULTY → REASSESS → UPDATE MASTERY → UPDATE LEARNING PATH → RECOMMEND NEXT ACTION**

Built for Smart India Hackathon 2026.

---

## The problem being solved

Most students follow a one-size-fits-all syllabus regardless of what they actually know. ELEVATE AI instead builds a picture of each student's real understanding — topic by topic — and continuously adapts what they see next: easier material and hints where they're struggling, harder application questions where they're strong, and clear visibility for teachers into where a whole class is stuck.

**Every number in this app is calculated from real stored data.** No progress bar, mastery score, streak, or accuracy figure is hardcoded. A new student starts at 0% / "Not Started" on everything, and every metric changes only because of real quiz attempts, assessment submissions, and study activity logged to the database.

---

## Key features

- **Personalized learner profiling** — onboarding collects academic info, subjects, goals and preferences, then an initial diagnostic assessment establishes an honest starting point (no artificial head start).
- **Topic-level knowledge-gap detection** — automatically flags topics where recent accuracy is low or declining, with common mistakes and recommended next actions.
- **Adaptive learning path** — a visual roadmap (Not Started → In Progress → Developing → Needs Revision → Completed → Mastered) that changes as performance changes.
- **AI Tutor** — Socratic, hint-first tutoring (never just gives the final answer), with actions for Hint / Simpler Explanation / Example / Summarize / Practice / Generate Quiz. Runs in a fully offline **Demo AI Mode** by default, or can call a real LLM if `AI_API_KEY` is set.
- **RAG on uploaded study material** — PDFs/notes are parsed (PyMuPDF), chunked, and retrieved via lightweight keyword-overlap search; AI Tutor and quiz answers are grounded in your own material and clearly labeled "Grounded in: filename," with an honest "I couldn't find this in your document" fallback rather than hallucinating a source-based answer.
- **MCQ & Quiz Generation** — bank-based quizzes (Easy/Medium/Hard/Adaptive) across conceptual, application, numerical and scenario question types, plus Recommended / Quick / Topic / Weak-Area / Previous-Mistakes / Daily / Custom / Material-grounded modes.
- **Adaptive Assessments** — diagnostic, recommended, topic, revision and adaptive assessment types with timer, mark-for-review, and mastery-before/after comparison.
- **Knowledge Graph** — an interactive canvas visualization (pure vanilla JS, pan/zoom/click, no external graphing library required) of a student's topics and prerequisite relationships.
- **Learning Analytics** — weekly activity, quiz accuracy trend, topic mastery and improvement, all rendered from backend-calculated data with genuine empty states when there isn't enough history yet.
- **Teacher oversight** — class analytics, per-student drill-down, and an AI Recommendation Review workflow (Approve / Edit / Regenerate / Reject) that makes clear AI assists but does not replace the teacher.

---

## Technology stack

- **Frontend:** HTML5, CSS3, Vanilla JavaScript only (no frameworks). Canvas-based charts and knowledge graph, no external chart/graph library dependency required.
- **Backend:** Python + FastAPI, modular routes/services/schemas/models.
- **Database:** SQLite (via SQLAlchemy ORM — swap `DATABASE_URL` to a Postgres URL to migrate; no SQLite-specific query syntax is used in the models).
- **Document processing:** PyMuPDF for PDF text extraction; a deterministic regex-based concept extractor (no LLM dependency required for this to work).
- **Auth:** JWT bearer tokens (`python-jose`) + bcrypt password hashing (`passlib`).
- **AI:** Fully functional "Demo AI Mode" using rule-based, deterministic educational logic and the student's real stored data. Optionally connects to a real LLM (Anthropic Messages API by default) if `AI_API_KEY` is set in `.env` — falls back to Demo AI Mode automatically on any API error.

---

## Project structure

```
ELEVATE-AI/
  frontend/            HTML5 / CSS3 / Vanilla JS (static, servable by any web server)
    index.html, login.html, signup.html, onboarding.html, dashboard.html, ...
    css/  style.css, responsive.css, dashboard.css, tutor.css, quiz.css, assessment.css
    js/   api.js, auth.js, app.js, dashboard.js, onboarding.js, learningPath.js,
          knowledgeGaps.js, tutor.js, quiz.js, quizRunner.js, assessments.js,
          assessmentRunner.js, studyMaterials.js, knowledgeGraph.js, analytics.js, profile.js
  backend/
    main.py            FastAPI app entrypoint
    requirements.txt
    app/
      routes/          auth, student, quizzes, assessments, materials, tutor,
                        knowledge_graph, analytics, teacher, notifications
      models/           SQLAlchemy models (users, profiles, topics, questions,
                        quizzes, assessments, learning_events, knowledge_gaps,
                        recommendations, learning_paths, chat, knowledge graph, notifications, ...)
      schemas/          Pydantic request/response schemas
      services/         learner_model, quiz_engine, assessment_engine, document_engine,
                        tutor_engine, teacher_service, knowledge_graph
      database/         db.py (SQLAlchemy engine/session), seed.py (demo data)
      utils/            security.py (JWT + password hashing)
    uploads/             uploaded study materials land here
  database/              SQLite file lives here (elevate.db) once seeded/run
  .env.example
  README.md              (this file)
```

---

## Setup instructions

### 1. Backend

```bash
cd ELEVATE-AI/backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env         # edit if you want to set AI_API_KEY, etc.
```

### 2. Initialize the database with demo data

```bash
python -m app.database.seed
```

This creates `database/elevate.db`, seeds 3 subjects / 12 topics / ~60 real MCQ bank questions, and creates two demo accounts (see below). Demo student progress is produced by **actually running quizzes and an assessment through the real scoring engine** — not by writing numbers directly into the database — so every figure you see on first login is a genuine calculation.

### 3. Run the backend

```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API is now live at `http://localhost:8000`. Interactive API docs: `http://localhost:8000/docs`.

### 4. Run the frontend

The frontend is fully static — serve it with any static file server, e.g.:

```bash
cd ELEVATE-AI/frontend
python -m http.server 5500
```

Then open `http://localhost:5500/index.html`.

> The frontend calls the backend at `http://localhost:8000` by default (see `js/api.js`). To point it elsewhere, run this once in the browser console: `localStorage.setItem('elevate_api_base', 'https://your-backend-url')`.

---

## Environment variables (`.env`)

| Variable | Purpose | Required? |
|---|---|---|
| `JWT_SECRET` | Signs auth tokens | Yes (has a dev default) |
| `DATABASE_URL` | SQLAlchemy connection string | No (defaults to local SQLite) |
| `AI_API_KEY` | Enables a real LLM for the AI Tutor | No — app runs fully in Demo AI Mode without it |
| `AI_MODEL` | Which model to call if `AI_API_KEY` is set | No |

**API keys are never exposed to the frontend** — all AI calls happen server-side.

---

## Demo credentials

| Role | Email | Password |
|---|---|---|
| Student (Aarav Sharma) | `aarav.sharma@example.com` | `password123` |
| Teacher (Dr. Priya Mehta) | `priya.mehta@example.com` | `password123` |

Or click **Sign Up** to create your own account and go through onboarding + diagnostic yourself — you'll start at a genuine 0% on everything.

---

## Selected API endpoints

```
POST  /api/auth/register                 POST /api/auth/login          POST /api/auth/logout
GET   /api/student/profile               PUT  /api/student/profile
POST  /api/student/onboarding            GET  /api/student/dashboard
GET   /api/student/progress              GET  /api/student/mastery
GET   /api/student/learning-path         GET  /api/student/knowledge-gaps
GET   /api/student/recommendations
GET   /api/quizzes            POST /api/quizzes/generate     GET/POST /api/quizzes/{id}[/submit|/retry]
GET   /api/assessments        POST /api/assessments/build     GET/POST /api/assessments/{id}[/submit]
POST  /api/materials/upload   GET  /api/materials             GET /api/materials/{id}/knowledge-graph
POST  /api/tutor/chat         GET  /api/tutor/sessions
GET   /api/knowledge-graph    GET  /api/knowledge-graph/node/{topic_id}
GET   /api/analytics          GET  /api/notifications
GET   /api/teacher/students   GET  /api/teacher/analytics     GET/POST /api/teacher/recommendations
```

Full interactive schema: `http://localhost:8000/docs` (FastAPI auto-generated Swagger UI).

---

## How "no fabricated progress" is actually enforced

- Every quiz/assessment answer is stored individually (`quiz_answers`, `assessment_answers`) with correctness, difficulty and timestamp.
- `app/services/learner_model.py::calculate_topic_mastery` is the single function that turns those rows into a mastery percentage, using recency-weighted, difficulty-weighted accuracy with a confidence penalty for small sample sizes — a topic with zero answers returns `mastery = 0, status = "not_started"`, never a placeholder number.
- Topic status (`not_started` / `in_progress` / `developing` / `needs_revision` / `completed` / `mastered`) is derived from that same calculation — opening a page or a PDF never marks something complete.
- Streaks only increment once per day, and only when a meaningful event (quiz, assessment, material completion, tutor session, etc.) is logged — visiting the dashboard does not extend a streak.
- Every dashboard/analytics/teacher endpoint calls into this same service layer, so the frontend always renders what the backend actually computed.

---

## Responsible AI

- **AI-generated information can contain errors.** Explanations, hints and demo-mode tutoring responses are produced by rule-based logic or an LLM and should be checked, not treated as infallible.
- **Mastery scores are estimates of current understanding, not absolute measurements of ability.** They can go up or down as new evidence comes in, and are most meaningful with more attempts behind them.
- **Student data is handled responsibly.** Passwords are hashed (never stored in plain text); the AI Tutor never fabricates a source-grounded claim — if the answer isn't in a student's uploaded material, it says so.
- **Important educational decisions should not rely entirely on automated predictions.** Teachers can inspect any student's real activity and must Approve, Edit, Regenerate or Reject every AI-generated recommendation before it's acted on.
- **AI is designed to support — not replace — human teaching.** The Teacher Recommendation Review workflow keeps a human in the loop at every step.

---

## Known scope notes

This is a hackathon-scale build of a genuinely large product spec. A few areas are intentionally kept simple rather than gold-plated, and are good next steps for a v2:
- The concept extractor for uploaded PDFs uses a deterministic regex pattern (`X is/are/means Y`) rather than an LLM-based extractor — reliable and dependency-free, but it will miss concepts phrased differently. Wire in `AI_API_KEY` and extend `document_engine.py` to use the LLM for richer extraction.
- RAG retrieval uses lightweight keyword-overlap scoring rather than embeddings — accurate for short, focused documents; swap in a vector store for larger corpora.
- The question bank ships with curated MCQs across 3 subjects / 12 topics as a demonstration set — the generation pipeline (topic/difficulty/type selection, adaptive logic, material-grounded generation) is fully general and designed to scale to a much larger bank or LLM-generated questions.
