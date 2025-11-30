ARCHITECTURE.md
System Architecture for the Recruiting SaaS Platform

This document describes the architecture of the recruiting platform:

High-level system design

Backend architecture (FastAPI)

Frontend architecture (Streamlit)

Data model

Matching engine

Agent (chat) behavior

File/AI-assisted flows (job req + resume)

1. High-Level Overview

The system is a two-tier web application:

Backend (FastAPI)

REST API

Authentication + org/user management

Jobs, Candidates, Applications CRUD

Matching engine (job ↔ candidate)

Agent “orchestrator” (LangGraph-style intent routing)

AI-assisted extraction flows (job reqs, resumes)

Frontend (Streamlit)

UI for authentication

Chat interface with recruiter assistant

Jobs & candidates overview

Matching visualization (tables)

File upload flows (job req → job, resume → candidate)

Communication: HTTP/JSON over the internal network (or Docker bridge) between Streamlit and FastAPI.

2. Backend Architecture (FastAPI)
2.1 Structure

backend/app/:

core/

config.py – global settings (Settings via Pydantic BaseSettings)

database.py – SQLAlchemy engine/session and Base

security.py – password hashing + JWT creation

models/ – SQLAlchemy models (ORM)

schemas/ – Pydantic models (request/response types)

services/ – business logic & AI utilities

api/

deps.py – common dependencies (get_db, get_current_user)

routes/ – router modules grouped by domain

main.py – FastAPI app, CORS, router wiring

2.2 Important Modules
core.config

Centralized configuration:

DB URL (e.g., SQLite in dev)

CORS origins

JWT secret and algorithm

OpenAI API configuration

Feature toggles (e.g., MATCHING_USE_OPENAI)

core.database

Creates SQLAlchemy engine and SessionLocal

Defines base declarative_base() as Base

core.security

get_password_hash / verify_password using passlib[bcrypt]

create_access_token using python-jose (JWT)

api.deps

get_db: per-request SQLAlchemy session

get_current_user: reads JWT, decodes, looks up user

3. Data Model
3.1 Entities
Organization

models/organization.py

id, name, slug, plan

Relationships: users, jobs, candidates, applications, match_logs

User

models/user.py

id, org_id, email, password_hash, full_name, role

role (e.g., org_admin, recruiter, candidate)

Relationship to Organization

Candidate

models/candidate.py

Core identity:

id, org_id, user_id?

full_name, headline, location, experience_years

current_title, current_company

Links:

linkedin_url, github_url, website_url

notes – arbitrary summary / extracted info

Timestamps: created_at, updated_at

Relationships:

org, applications, match_logs

Job

models/job.py

Core:

id, org_id, created_by_user_id

title, department, location, employment_type, remote_option

Compensation:

salary_min, salary_max, currency

Description:

description

required_skills (JSON array)

nice_to_have_skills (JSON array)

State:

status (open, on_hold, closed, etc.)

is_public bool

Timestamps

Relationships:

org, created_by, applications, match_logs

Application

models/application.py

Core:

id, org_id

job_id, candidate_id

Pipeline:

status (e.g., sourced, applied, screening, offer, hired)

source (e.g., manual, referral, import)

fit_score (int)

Timestamps

Relationships:

org, job, candidate

MatchLog

models/match_log.py

Used to keep track of how/why a match was computed:

org_id, job_id, candidate_id

score (0–100)

strategy ("naive" or "openai")

reason (human-readable explanation)

created_at

4. API Layer

All routes live under backend/app/api/routes/ and are assembled into api_router in __init__.py, then included in main.py with prefix /api/v1.

4.1 Auth & Users

auth.py

POST /auth/register – create org + first user

POST /auth/login – JWT token (OAuth2 password flow)

users.py

GET /users/me – current user details

4.2 Jobs

jobs.py

GET /jobs – list (filter by status/query)

POST /jobs – create

GET /jobs/{id}

PATCH /jobs/{id}

DELETE /jobs/{id}

4.3 Candidates

candidates.py

GET /candidates – list + search

POST /candidates – create

GET /candidates/{id}

PATCH /candidates/{id}

DELETE /candidates/{id}

4.4 Applications

applications.py

GET /applications – filter by job/candidate

POST /applications – create (job + candidate)

GET /applications/{id}

PATCH /applications/{id}

DELETE /applications/{id}

4.5 Matching

matching.py

POST /matching/candidates_for_job

Returns ranked candidate matches for a job

Logs each match in match_logs

POST /matching/jobs_for_candidate

Returns ranked job matches for a candidate

Logs each match

4.6 Agent & AI-assisted Flows

agent.py

POST /agent/chat

Consumes a message and returns a text reply

agent_jobs.py

POST /agent/jobs/from_prompt

Converts free-text job description into a structured Job

POST /agent/jobs/from_req

Accepts uploaded job req file (e.g., text, doc, etc.)

Uses AI (if enabled) to parse and create a Job

Responds with a human-readable summary and the Job payload

agent_candidates.py

POST /agent/candidates/from_resume

Accepts uploaded resume

Uses AI (if enabled) to parse and create a Candidate

Responds with summary & candidate data

5. Service Layer
5.1 Matching Service

File: services/matching.py

Responsibilities:

Normalize text fields into keyword sets

Compute naive matches (keyword overlap between job and candidate)

Compute embedding-based matches (OpenAI, optional)

Provide two main entrypoints:

rank_candidates_for_job(db, org_id, job_id, limit) -> list[CandidateMatch]
rank_jobs_for_candidate(db, org_id, candidate_id, limit) -> list[JobMatch]

Naive flow (fallback / default):

Collect keywords from:

Job: title, required_skills, nice_to_have_skills

Candidate: current_title, headline, current_company

Compute overlap ratio:

score = len(overlap) / len(job_keywords) * 100

Score range: 0–100 (int), plus a reason: "Keyword overlap on: X, Y, Z"

OpenAI embedding flow (optional):

Build textual representations:

Job text (title + description + skills)

Candidate text (name + titles + company + location)

Call OpenAI embeddings with [job_text, candidate_texts...] or [candidate_text, job_texts...]

Compute cosine similarity between vectors

Map similarity to score (0–100)

Generate reason using overlap + explanation text

Use when:

MATCHING_USE_OPENAI==true and OPENAI_API_KEY is set

Fallback to naive on any AI failure

5.2 Agent Jobs

File: services/agent_jobs.py

Responsibilities:

Turn a prompt or job req text into a structured Job record:

If OpenAI is enabled, uses chat completion to return JSON with keys:

title, department, location, employment_type, remote_option, salary_min, salary_max, currency, description, required_skills, nice_to_have_skills

Fallback: treat prompt as description + truncated title

Exposed as:

create_job_from_prompt

create_job_from_req (file → text → struct)

5.3 Agent Candidates

File: services/agent_candidates.py

Responsibilities:

Turn resume text into structured Candidate:

AI mode: instructs OpenAI to output JSON:

full_name, headline, location, experience_years, current_title, current_company, linkedin_url, github_url, website_url, notes

Fallback: naive – first non-empty line as name, first lines as notes

Stores notes with optional extra recruiter notes

Exposed as:

create_candidate_from_resume

5.4 Agent Orchestrator

File: services/agent.py

This is a single-process “agent” that:

Accepts a message + user + db

Uses simple intent detection based on lowercased keywords

Calls services / queries DB accordingly

Returns a plain-text reply rendered by the UI

Supported intents:

Create job from prompt

Triggers on patterns like "create a new job", "new job", "open a role", etc.

Calls create_job_from_prompt

Summarize candidate

"summarize candidate 3", "who is candidate #5", etc.

Looks up candidate by ID and formats a summary

Match candidates for job

"match candidates for job 5", "best candidates for job 2", etc.

Uses rank_candidates_for_job, formats explanation

Match jobs for candidate

"match jobs for candidate 7", "jobs for candidate #3", etc.

Uses rank_jobs_for_candidate, formats explanation

List jobs / open jobs

"list jobs", "open jobs", "show jobs"

List candidates

"list candidates", "show candidates"

Show applications pipeline for job

"applications for job 10", "pipeline for job #3"

Fallback help

If no intent is matched, reply with usage hints and echo the user input

The agent is intentionally stateless per call (no conversation history persisted), but can be extended easily to store transcripts.

6. Frontend Architecture (Streamlit)
6.1 Structure

frontend/:

streamlit_app.py – main entrypoint, simple landing page

pages/

01_Auth_Login.py – login + registration

02_App_Chat.py – recruiter chat + job-req upload

03_Jobs.py – placeholder for job management UI

04_Candidates.py – placeholder for candidate management UI

05_Jobs_and_Candidates.py – job↔candidate matching views

06_New_Candidate_From_Resume.py – resume upload → candidate creator

utils/api_client.py – simple HTTP client for backend

6.2 State Management

Streamlit uses st.session_state for:

api_client – instance of APIClient with current token

access_token – JWT

current_user – user info (id, email, org)

chat_messages – list of messages for chat page

candidate_chat – messages for resume page summary

6.3 Key UI Flows
Auth Page (01_Auth_Login.py)

Tabs: Login & Register

Login:

Calls /auth/login

Saves token + user info

Register:

Calls /auth/register

Recruiter Chat (02_App_Chat.py)

Left panel: chat history + st.chat_input

Right panel:

Quick command buttons (list jobs, list candidates, etc.)

Job req upload:

file_uploader for JD

Optional notes

Button → calls /agent/jobs/from_req

Injects “user uploaded file” + agent summary messages into chat

Jobs & Candidates Matching (05_Jobs_and_Candidates.py)

Top: Job → Candidates

Filters: job status, search by title

Select job from dropdown

Button: “Find candidate matches”

Shows pandas.DataFrame with matches (score, strategy, reason)

Bottom: Candidate → Jobs

Fetch candidates

Select candidate

Button: “Find job matches”

Shows DataFrame with job matches

New Candidate from Resume (06_New_Candidate_From_Resume.py)

Upload resume + optional notes

Call /agent/candidates/from_resume

Show:

Success message

Summary of candidate

Seeded “assistant” chat messages showing what was created

Right column: read-only explanation/instruction on how to use this candidate in Recruiter Chat (e.g., “summarize candidate N”)

7. File / AI Flows
7.1 Job Req Upload → Job

User uploads job description file in 02_App_Chat.py.

Frontend calls APIClient.create_job_from_req(...).

Backend:

/agent/jobs/from_req endpoint:

Reads file bytes

Decodes to text

Optionally appends recruiter notes

Calls create_job_from_req(...):

AI extraction (if enabled) or naive fallback

Creates Job row

Returns Job + summary string.

Frontend:

Appends pseudo “user” and “agent” messages to chat.

Shows success toast.

7.2 Resume Upload → Candidate

User uploads resume in 06_New_Candidate_From_Resume.py.

Frontend calls APIClient.create_candidate_from_resume(...).

Backend:

/agent/candidates/from_resume endpoint:

Reads bytes, decodes

Calls create_candidate_from_resume(...):

AI extraction (if enabled) or naive fallback

Creates Candidate row

Builds summary string.

Frontend:

Shows summary & candidate details.

Seeds candidate_chat suggestions.

Provides guidance to query the agent: summarize candidate {id}.

8. Non-Functional Aspects
8.1 Security

JWT-based auth for all protected endpoints

Passwords hashed with bcrypt

CORS restricted via BACKEND_CORS_ORIGINS (default: local Streamlit)

8.2 Scalability

Stateless FastAPI app:

Horizontally scalable

DB becomes shared bottleneck – can swap SQLite for Postgres/MySQL

Streamlit frontend:

Can be containerized and scaled behind a load balancer

Matching/AI:

Currently synchronous per request

Could be offloaded to background workers (Celery/RQ) if needed

8.3 Extensibility

Add new endpoints by:

Creating router files under api/routes

Registering them in api/routes/__init__.py

Add new agent skills by:

Extending run_agent_chat in services/agent.py

Add new models:

Add SQLAlchemy model

Add corresponding schema(s)

Add migration or re-create DB in dev

9. Typical Request Flows (Examples)
9.1 “Match candidates for job 5” via Chat

Streamlit sends:

POST /agent/chat with { message: "match candidates for job 5" }

Agent:

Parses job_id=5

Calls rank_candidates_for_job(...)

Formats explanation text

Response:

Chat message describing top matches, including scores and reasons

9.2 “Match jobs for candidate 7” via Jobs & Candidates Page

Streamlit gets candidate_id=7 from dropdown.

Calls:

POST /matching/jobs_for_candidate { candidate_id: 7 }

Matching service:

Computes matches

Response:

List of jobs with scores & reasons

Streamlit:

Shows results in a table

10. How to Modify or Build On This

To add new agent behaviors: expand run_agent_chat with new keyword patterns + logic.

To add new AI models: adjust services/matching.py and services/agent_* to call different LLMs/embedding endpoints.

To support multi-tenant UI features: add org-specific filters to all listing endpoints & UI.

To integrate with external ATS/CRMs: build connectors in services/ and new routes under api/routes/, then expose via UI.

This architecture is intentionally modular and pragmatic: you can keep everything simple for now, while still having clear seams to scale into a more complex, multi-service system later (worker queues, event-driven, etc.).