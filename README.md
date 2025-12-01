# Recruiting Platform – Developer Guide (Quickstart)

## 🚀 Get started fast (Docker Compose)
```bash
git clone https://github.com/joestein/recruiting-platform.git
cd recruiting-platform

# Optional: copy env and adjust secrets/keys
cp .env.example .env

# Bring up backend + frontend (+ AGE graph)
docker compose -f infra/docker-compose.yml up --build

# Services
# - Backend API: http://localhost:8000 (docs at /docs)
# - Frontend (Streamlit): http://localhost:8501
# - AGE (graph, for Q&A/traits): localhost:5432
```

## 🔧 Local dev without Docker
- Backend: see `backend/README.md` (uv + uvicorn).
- Frontend: see `frontend/README.md` (uv + streamlit).
- Ensure `.env` has correct `API_URL`/DB/graph settings.

## 🧠 What’s inside
- FastAPI backend: auth/org management, jobs, candidates, applications, matching, agents, Q&A router.
- Streamlit frontend: auth, recruiter chat, job/candidate pages, matching views, uploads.
- AI/agents: LangGraph router, Q&A flows (YAML-defined), general chat, calendar stub; Instructor-based classification; graph-backed traits (AGE locally, Neptune-ready).
- Infra: Dockerfiles, Compose (backend, frontend, AGE), OpenAI optional.

## 📂 Repo layout
- `backend/` — FastAPI app (`app/main.py`, `api/`, `services/`, `qna_graph/`, `agents/`).
- `frontend/` — Streamlit app (`streamlit_app.py`, `pages/`, `utils/api_client.py`).
- `infra/` — Dockerfiles, docker-compose.yml.
- `docs/` — Q&A graph and AGE local dev guides.
- `.env.example` — config template (DB, OpenAI, graph).

## ✨ Contributing (short version)
- Fork & branch; use uv for Python deps (`uv sync`), no pip.
- Run lint/tests locally if added.
- Open a PR with clear description/screenshots for UI.

---

# Welcome Contributors

This project builds an AI-assisted recruiting platform in public. If you contribute, you’re a partner— not “free labor.” I actively surface strong contributors to hiring teams and help with intros and interview prep.

## What you gain
- Visibility to teams hiring.
- Warm introductions when you’re ready.
- Interview coaching and practical feedback.
- Real-world, production-grade experience (FastAPI, Streamlit, AI/agents, matching, AWS).

## What we’re building
- Create jobs from prompts or uploads; parse resumes to structured profiles.
- Match candidates ↔ jobs with explainable scoring.
- Multi-step recruiter agent chat with Q&A flows.
- Clean REST API + Streamlit UI; OpenAI-enhanced flows (optional).

## How to get involved
- Star/fork the repo.
- If the platform isn’t live yet, connect on LinkedIn and share your resume; grab an open GitHub issue if you see a fit.

## Stack snapshot
- Backend: Python, FastAPI, SQLAlchemy, Pydantic, LangGraph.
- Frontend: Streamlit.
- DB: SQLite (dev) → Postgres (prod); AGE graph locally; Neptune-ready.
- AI: OpenAI embeddings/structured extraction (optional).
- Infra: Docker; App Runner/ECS/K8s in sight.

## Roadmap highlights
- Matching 2.0; candidate pools; interview/outreach helpers.
- ATS integrations; plugins; public API; webhooks; scorecard marketplace.

## Final note
This is a community building something real. If you put in good work, I’ll advocate for you, introduce you to teams, and help you land roles. Let’s build the future of recruiting together.***
