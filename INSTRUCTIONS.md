# Developer Guide – Recruiting SaaS Platform

Welcome to the Codex-powered Recruiting SaaS Platform. This guide covers how to run, extend, and deploy the project.

## 1) Overview
- Full-stack recruiting platform with FastAPI backend + Streamlit frontend.
- Features: job creation (manual/AI), candidate creation (manual/AI from resumes), job↔candidate matching (naive or OpenAI embeddings), recruiter chat agent, org/user management, applications, match logs.
- Optional OpenAI integration for embeddings and structured extraction.

## 2) Repo Structure
```
recruiting-platform/
├── backend/
│   └── app/
│       ├── core/       # Config, DB, security
│       ├── models/     # SQLAlchemy models
│       ├── schemas/    # Pydantic models
│       ├── services/   # Matching + AI agent logic
│       ├── api/        # FastAPI routers
│       └── main.py     # FastAPI entrypoint
├── frontend/
│   ├── streamlit_app.py
│   ├── pages/          # Streamlit multipage UI
│   └── utils/api_client.py
├── infra/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
├── .env.example
└── INSTRUCTIONS.md
```

## 3) Prerequisites
- Python 3.11+
- Docker + Docker Compose (optional but recommended)
- OpenAI API key (optional; needed for embeddings/structured extraction)
- Streamlit; FastAPI + Uvicorn

## 4) Running Locally
**Option A: Local Python**
- Backend:
  - `cd backend`
  - `cp ../.env.example .env` (optional)
  - `uvicorn app.main:app --reload --port 8000`
  - Open: http://localhost:8000/docs
- Frontend:
  - `cd frontend`
  - `streamlit run streamlit_app.py`
  - Open: http://localhost:8501

**Option B: Docker Compose (recommended)**
- From repo root: `docker compose -f infra/docker-compose.yml up --build`
- Services:
  - Backend: http://localhost:8000
  - API docs: http://localhost:8000/docs
  - Frontend: http://localhost:8501
- Stop: `docker-compose down`; detached: `docker-compose up -d`.

## 5) Environment Variables
`.env.example` includes:
```
SECRET_KEY=CHANGE_ME
SQLALCHEMY_DATABASE_URI=sqlite:///./dev.db
BACKEND_CORS_ORIGINS=http://localhost:8501
OPENAI_API_KEY=
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4o-mini
MATCHING_USE_OPENAI=false
```
- Set `MATCHING_USE_OPENAI=true` to enable embeddings-based matching.
- Set `OPENAI_API_KEY` for AI job/candidate extraction.

## 6) Core Features
- **Auth:** org + user registration, JWT login, current user profile.
- **Jobs:** CRUD; AI-assisted creation from prompt or uploaded job req.
- **Candidates:** CRUD; AI-assisted creation from resume upload → structured record.
- **Matching:** naive keyword or OpenAI embeddings; endpoints `/matching/candidates_for_job`, `/matching/jobs_for_candidate`; logs stored for audit.
- **Recruiter Chat Agent:** commands like “create a new job…”, “match candidates for job 5”, “list jobs”, “summarize candidate 3”; LangGraph-style routing.
- **Streamlit UI:** login/register, chat, job/candidate search, matching views, resume and job-req uploads; all via backend REST.

## 7) How to Extend
### 7.1 Add agent skills
- File: `backend/app/services/agent.py`
- Pattern: keyword detection → parsing → DB/service calls → text reply.

### 7.2 Add REST endpoints
- Create router: `backend/app/api/routes/my_feature.py`
- Register in: `backend/app/api/routes/__init__.py`
- Follow existing router patterns.

### 7.3 Add models
- SQLAlchemy model: `backend/app/models/`
- Pydantic schema: `backend/app/schemas/`
- Dev uses auto-create; for prod add migrations (see §8/9).

### 7.4 Modify matching
- File: `backend/app/services/matching.py`
- Add custom scoring, normalization, weighting, embeddings caching, resume parsing hooks.

### 7.5 Extend Streamlit
- Add pages under `frontend/pages/`
- Use `APIClient` (`from utils.api_client import APIClient`)
- Build tables, forms, wizards, chat workflows.

## 8) Deployment Options
- **Docker on EC2/VM:** build backend/frontend images; front with Nginx → containers.
- **AWS App Runner:** deploy backend + frontend containers; ensure WSS for Streamlit.
- **Kubernetes:** scale recruiter agent, matching workers, file ingestion workers, schedulers (Celery/Huey/RQ).

## 9) Roadmap Ideas
- Resume parser (OpenAI + heuristics) for skills/titles/dates/seniority/timeline.
- Skills tagging/normalization (taxonomy + embeddings).
- Matching 2.0: weighted, hybrid semantic/structured, diversity prefs, recruiter overrides.
- Applications workflow: pipeline stages, automations, feedback, scorecards.
- Teams/permissions: multi-user org, job owners, candidate pool restrictions.
- Billing: Stripe metered (per job/match/AI call).
- Analytics: time-to-fill, source-of-hire, funnel conversion.

## 10) Using Codex
- Ask Codex to generate routers, extend models, add validation/endpoints, tweak matching, extend Streamlit, integrate external APIs (LinkedIn/Greenhouse/Lever), write migrations/tests, produce diagrams, build onboarding flows, or marketing copy.
- Example prompt: “Add a new `/experience` router for candidate job history with CRUD, integrate into matching, and add a Streamlit page to manage experience records.”

## 11) Summary
- Full recruiting SaaS skeleton: AI job creation, AI candidate creation, matching engine, recruiter chat, FastAPI backend, Streamlit frontend, Dockerized deployment, and extensible architecture for Codex-driven development.
