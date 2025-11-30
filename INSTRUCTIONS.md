Developer Guide for the Recruiting SaaS Platform (Codex Project)

Welcome to your Codex-powered Recruiting SaaS Platform.
This document outlines everything you need to know to run, extend, and build on the project.

1. Overview

This project is a full-stack recruiting platform designed to allow:

Job creation (manual or AI-assisted from natural language prompts and job-req uploads)

Candidate creation (manual or AI-assisted from resume uploads)

Matching between jobs and candidates (naive keyword match or OpenAI embeddings)

Interactive chat agent (LangGraph-style recruiter assistant)

Streamlit front-end for authentication, chat, job/candidate browsing, and matching views

FastAPI backend with full REST API

Organization, user, job, candidate, application, matching logs data model

Optional OpenAI integration for embeddings + chat/structured extraction

This setup gives you a ready-to-extend foundation for a SaaS recruiting product using Codex.

2. Repo Structure
recruiting-platform/
├── backend/
│   ├── app/
│   │   ├── core/             # Config, DB, Security
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic models
│   │   ├── services/         # Matching + AI Agent logic
│   │   ├── api/              # FastAPI routers
│   │   └── main.py           # FastAPI entrypoint
│   ├── pyproject.toml
│   └── README.md
│
├── frontend/
│   ├── streamlit_app.py
│   ├── pages/                # Streamlit multipage UI
│   ├── utils/api_client.py
│   ├── requirements.txt
│   └── README.md
│
├── infra/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
│
├── .env.example
└── INSTRUCTIONS.md (this file)

3. Prerequisites

You need:

Python 3.11+

Docker + Docker Compose (optional but recommended)

OpenAI API key (optional, only needed for embedding-based matching & structured extraction)

Streamlit

FastAPI + Uvicorn

4. Running the Project (Local Dev)
Option 1: Local Python
Backend:
cd backend
cp ../.env.example .env   # optional
uvicorn app.main:app --reload --port 8000


Go to:
➡️ http://localhost:8000/docs

Frontend:
cd frontend
streamlit run streamlit_app.py


Go to:
➡️ http://localhost:8501

Option 2: Docker Compose (recommended)

From repo root:

docker compose -f infra/docker-compose.yml up --build


This starts:

Service	URL
Backend	http://localhost:8000

API Docs	http://localhost:8000/docs

Frontend	http://localhost:8501
5. Environment Variables

.env.example includes:

SECRET_KEY=CHANGE_ME
SQLALCHEMY_DATABASE_URI=sqlite:///./dev.db
BACKEND_CORS_ORIGINS=http://localhost:8501

# OpenAI (optional)
OPENAI_API_KEY=
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4o-mini
MATCHING_USE_OPENAI=false


Set:

MATCHING_USE_OPENAI=true to enable vector matching

OPENAI_API_KEY for AI job/candidate extraction

6. Core Features
✔️ Authentication

Register user + organization

JWT login

Current user / profile endpoint

✔️ Jobs

CRUD jobs

AI-assisted job creation

From prompt

From uploaded job req file

✔️ Candidates

CRUD candidates

AI-assisted candidate creation

Upload resume → structured candidate record

✔️ Matching Engine

Modes:

Naive keyword overlap

OpenAI embeddings (optional)

Endpoints:

/matching/candidates_for_job

/matching/jobs_for_candidate

Matching logs recorded for auditability.

✔️ Recruiter Chat Agent

Understands commands like:

"create a new job for a senior backend engineer"
"match candidates for job 5"
"list jobs"
"summarize candidate 3"


Backed by LangGraph-inspired routing logic.

✔️ Streamlit UI

Login/Register

AI Chat assistant

Jobs & Candidates search

Matching UI

Resume upload → new candidate creation

Job req upload → new job creation

All functions call backend over REST.

7. How to Extend

This is the important section for ongoing work.

7.1 Add new agent skills

Add new handlers in:

backend/app/services/agent.py


Pattern:

if "some command" in lower:
    # handle it


Add:

parsing

database interactions

domain logic

Then reply with a message the chat UI will render.

7.2 Add new REST endpoints

Create a new router file:

backend/app/api/routes/my_feature.py


Register it in:

backend/app/api/routes/__init__.py


Follow existing router patterns.

7.3 Add new models

Add SQLAlchemy model:

backend/app/models/


Add Pydantic schema:

backend/app/schemas/


Run migrations manually (SQLite auto-creates on import).

7.4 Modify matching logic

Edit:

backend/app/services/matching.py


You can add:

custom scoring

skills normalization

weighting (title vs description vs experience)

resume parsing integrations

embeddings caching

7.5 Extend Streamlit frontend

Add new pages under:

frontend/pages/


Use the API client:

from utils.api_client import APIClient
api = APIClient(access_token)


Add:

new tables

forms

wizards

chat workflows

8. Deployment Strategy
Option 1: Docker on EC2 or VM

Build backend image

Build frontend image

Point domain → Nginx → containers

Option 2: AWS App Runner

Frontend: Streamlit container

Backend: FastAPI container

Enable WSS (Streamlit websocket needs this)

Option 3: Kubernetes

Good for scaling:

Recruiter agent service

Matching workers

File ingestion workers

Background job scheduler (Celery/Huey/RQ)

9. Future Enhancements (Roadmap)

These are natural next steps for this project:

🔹 Resume Parser (OpenAI + custom heuristics)

Extract:

Skills

Titles

Dates

Companies

Seniority estimation

Job history timeline

🔹 Skills Tagging & Normalization

Graph-based taxonomy + embeddings.

🔹 Matching 2.0

Weighted scoring

Fine-tuned model

Semantic + structured hybrid

Diversity preferences

Recruiter override scoring

🔹 Applications Workflow

Pipeline stages

Automations (“email candidate next step”)

Feedback collection

Scorecards

🔹 Teams & Permissions

Multi-user org support

Job owners

Candidate pool restriction

🔹 Billing

Stripe metered billing

per job

per match

per AI call

🔹 Analytics Dashboard

Time-to-fill

Source-of-hire

Funnel conversion metrics

10. Using Codex to Continue Development

Once you're inside the Codex environment:

Ask Codex to:

generate new Python routers

extend models

add validation

implement new endpoints

modify matching logic

extend Streamlit UI

integrate external APIs (LinkedIn, Greenhouse, Lever)

write migrations

add tests

produce UML diagrams

build full user onboarding flows

produce marketing site copy

Codex prompt example:
Add a new /experience router that stores candidate job history. 
It should support CRUD and also integrate into the matching logic.
Also add a Streamlit page to manage experience records.

11. Summary

You now have:

A full recruiting SaaS skeleton

With AI job creation, AI candidate creation, matching engine, agent chat

Fully wired FastAPI backend + Streamlit frontend

Dockerized for easy deployment

Extensible architecture for Codex-driven development

This INSTRUCTIONS.md is your blueprint for building the full product.