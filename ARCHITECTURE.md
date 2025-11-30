# System Architecture for the Recruiting SaaS Platform

This document outlines the architecture of the recruiting platform across backend, frontend, data, AI flows, and extensibility.

## 1. High-Level Overview

- Two-tier web app: FastAPI backend + Streamlit frontend.
- Communication: HTTP/JSON over internal network (or Docker bridge).
- Core capabilities: auth/org management, jobs/candidates/applications CRUD, matching engine, agent-style chat, and AI-assisted file ingestion.

## 2. Backend Architecture (FastAPI)

**Project structure (`backend/app/`):**
- `core/`
  - `config.py`: global settings (Pydantic `BaseSettings`).
  - `database.py`: SQLAlchemy engine/session and `Base`.
  - `security.py`: password hashing + JWT creation.
- `models/`: SQLAlchemy ORM models.
- `schemas/`: Pydantic request/response models.
- `services/`: business logic and AI utilities.
- `api/`
  - `deps.py`: common dependencies (`get_db`, `get_current_user`).
  - `routes/`: routers grouped by domain.
- `main.py`: FastAPI app setup, CORS, router wiring.

**Key modules:**
- `core.config`: DB URL, CORS origins, JWT settings, OpenAI config, feature toggles (e.g., `MATCHING_USE_OPENAI`).
- `core.database`: engine and `SessionLocal`, declarative `Base`.
- `core.security`: `get_password_hash`/`verify_password` (passlib[bcrypt]), `create_access_token` (python-jose JWT).
- `api.deps`: request-scoped DB session, current user resolution.

## 3. Data Model

**Organization** (`models/organization.py`): `id`, `name`, `slug`, `plan`; relationships to users, jobs, candidates, applications, match_logs.

**User** (`models/user.py`): `id`, `org_id`, `email`, `password_hash`, `full_name`, `role` (e.g., `org_admin`, `recruiter`, `candidate`); relationship to organization.

**Candidate** (`models/candidate.py`):
- Identity: `id`, `org_id`, `user_id?`, `full_name`, `headline`, `location`, `experience_years`, `current_title`, `current_company`.
- Links: `linkedin_url`, `github_url`, `website_url`.
- `notes`, `created_at`, `updated_at`.
- Relationships: org, applications, match_logs.

**Job** (`models/job.py`):
- Core: `id`, `org_id`, `created_by_user_id`, `title`, `department`, `location`, `employment_type`, `remote_option`.
- Compensation: `salary_min`, `salary_max`, `currency`.
- Description: `description`, `required_skills` (JSON array), `nice_to_have_skills` (JSON array).
- State: `status` (open, on_hold, closed, etc.), `is_public`.
- Timestamps; relationships to org, creator, applications, match_logs.

**Application** (`models/application.py`):
- Core: `id`, `org_id`, `job_id`, `candidate_id`.
- Pipeline: `status` (sourced → hired), `source` (manual, referral, import), `fit_score`.
- Timestamps; relationships to org, job, candidate.

**MatchLog** (`models/match_log.py`):
- `org_id`, `job_id`, `candidate_id`, `score` (0–100), `strategy` ("naive" or "openai"), `reason`, `created_at`.

## 4. API Layer

Routers live under `backend/app/api/routes/`, assembled into `api_router` (in `api/routes/__init__.py`), and included in `main.py` with prefix `/api/v1`.

**Auth & Users**
- `auth.py`: `POST /auth/register` (create org + first user), `POST /auth/login` (JWT via OAuth2 password).
- `users.py`: `GET /users/me`.

**Jobs**
- `jobs.py`: `GET /jobs`, `POST /jobs`, `GET /jobs/{id}`, `PATCH /jobs/{id}`, `DELETE /jobs/{id}`.

**Candidates**
- `candidates.py`: `GET /candidates`, `POST /candidates`, `GET /candidates/{id}`, `PATCH /candidates/{id}`, `DELETE /candidates/{id}`.

**Applications**
- `applications.py`: `GET /applications`, `POST /applications`, `GET /applications/{id}`, `PATCH /applications/{id}`, `DELETE /applications/{id}`.

**Matching**
- `matching.py`: `POST /matching/candidates_for_job` (ranked candidates for a job, logs matches), `POST /matching/jobs_for_candidate` (ranked jobs for a candidate, logs matches).

**Agent & AI-assisted Flows**
- `agent.py`: `POST /agent/chat` (agent reply to a message).
- `agent_jobs.py`: `POST /agent/jobs/from_prompt` (free-text → Job), `POST /agent/jobs/from_req` (file upload → Job; AI parse with summary).
- `agent_candidates.py`: `POST /agent/candidates/from_resume` (resume upload → Candidate; AI parse with summary).

## 5. Service Layer

**Matching Service** (`services/matching.py`)
- Normalizes text to keyword sets; computes naive matches (keyword overlap) or embedding-based matches (OpenAI, optional).
- Entry points:
  - `rank_candidates_for_job(db, org_id, job_id, limit) -> list[CandidateMatch]`
  - `rank_jobs_for_candidate(db, org_id, candidate_id, limit) -> list[JobMatch]`
- Naive flow: collect keywords (job title/skills; candidate title/headline/company); score = overlap ratio * 100 with reason "Keyword overlap on: ...".
- OpenAI flow: build job/candidate text, call embeddings, cosine similarity → score (0–100); reason combines overlap + explanation. Uses `MATCHING_USE_OPENAI` toggle with fallback to naive.

**Agent Jobs** (`services/agent_jobs.py`)
- Prompt or job req text → structured Job record.
- AI mode: chat completion returns JSON fields (title, department, location, employment_type, remote_option, salary_min/max, currency, description, required_skills, nice_to_have_skills).
- Fallback: treat prompt as description with truncated title.
- Exposed as `create_job_from_prompt`, `create_job_from_req`.

**Agent Candidates** (`services/agent_candidates.py`)
- Resume text → structured Candidate.
- AI mode: chat completion returns JSON (full_name, headline, location, experience_years, current_title, current_company, linkedin_url, github_url, website_url, notes).
- Fallback: naive extraction (first non-empty line as name, early lines as notes).
- Exposed as `create_candidate_from_resume`; stores notes with optional recruiter notes.

**Agent Orchestrator** (`services/agent.py`)
- Stateless per-call “agent” that does intent detection (keyword-based) and routes to services/DB.
- Supported intents:
  - Create job from prompt (`create_job_from_prompt`).
  - Summarize candidate by ID.
  - Match candidates for job (`rank_candidates_for_job`).
  - Match jobs for candidate (`rank_jobs_for_candidate`).
  - List jobs / open jobs.
  - List candidates.
  - Show applications pipeline for job.
- Fallback: help text with usage hints and echo of input.

## 6. Frontend Architecture (Streamlit)

**Structure (`frontend/`):**
- `streamlit_app.py`: main entrypoint, landing.
- `pages/`
  - `01_Auth_Login.py`: login + registration.
  - `02_App_Chat.py`: recruiter chat + job-req upload.
  - `03_Jobs.py`: placeholder job management UI.
  - `04_Candidates.py`: placeholder candidate management UI.
  - `05_Jobs_and_Candidates.py`: job↔candidate matching views.
  - `06_New_Candidate_From_Resume.py`: resume upload → candidate creation.
- `utils/api_client.py`: simple HTTP client for backend.

**State management:** `st.session_state` holds `api_client`, `access_token`, `current_user`, `chat_messages`, `candidate_chat`.

**Key UI flows:**
- Auth page: login/register tabs; calls `/auth/login` or `/auth/register`; saves token + user.
- Recruiter chat: chat history + `st.chat_input`; quick command buttons; job req upload (file + notes) → `/agent/jobs/from_req`; injects pseudo chat messages and shows toast.
- Jobs & candidates matching: select job → “Find candidate matches” (shows DataFrame with score/strategy/reason); select candidate → “Find job matches.”
- New candidate from resume: upload resume + notes → `/agent/candidates/from_resume`; shows summary/details; seeds candidate chat suggestions and guidance for `summarize candidate {id}`.

## 7. File / AI Flows

**Job req upload → Job (02_App_Chat.py)**
- Frontend: upload file, optional notes; call `APIClient.create_job_from_req`.
- Backend: `/agent/jobs/from_req` reads bytes, decodes, appends notes, calls `create_job_from_req` (AI or fallback), creates Job, returns Job + summary.
- Frontend: appends pseudo “user”/“agent” chat messages, shows success toast.

**Resume upload → Candidate (06_New_Candidate_From_Resume.py)**
- Frontend: upload resume, optional notes; call `APIClient.create_candidate_from_resume`.
- Backend: `/agent/candidates/from_resume` decodes file, calls `create_candidate_from_resume` (AI or fallback), creates Candidate, builds summary.
- Frontend: shows summary/details, seeds candidate_chat suggestions, and guidance to query `summarize candidate {id}`.

## 8. Non-Functional Aspects

- **Security:** JWT-based auth; passwords hashed with bcrypt; CORS restricted via `BACKEND_CORS_ORIGINS` (default local Streamlit).
- **Scalability:** FastAPI is stateless/horizontally scalable; DB is shared bottleneck (SQLite → Postgres/MySQL); Streamlit can be containerized and scaled behind LB; matching/AI synchronous per request with potential worker offload (Celery/RQ).
- **Extensibility:** Add endpoints by creating routers under `api/routes` and registering; add agent skills by extending `run_agent_chat`; add models via SQLAlchemy model + schema + migration/DB refresh.

## 9. Typical Request Flows

**“Match candidates for job 5” via chat**
- Streamlit: `POST /agent/chat` with `{ message: "match candidates for job 5" }`.
- Agent: parse `job_id=5`, call `rank_candidates_for_job`, format explanation.
- Response: chat message with top matches, scores, reasons.

**“Match jobs for candidate 7” via Jobs & Candidates page**
- Streamlit: select candidate_id=7, call `POST /matching/jobs_for_candidate { candidate_id: 7 }`.
- Matching service computes matches; response lists jobs with scores/reasons; Streamlit shows table.

## 10. How to Modify or Build On This

- Add agent behaviors: extend `run_agent_chat` with new keyword patterns + logic.
- Add AI models: adjust `services/matching.py` and `services/agent_*` for alternate LLMs/embeddings.
- Support multi-tenant UI features: add org-specific filters to list endpoints + UI.
- Integrate with external ATS/CRMs: build connectors in `services/` + new routes under `api/routes/`, then expose via UI.
- Scale architecture: introduce worker queues/event-driven pieces for matching/AI as needed.
