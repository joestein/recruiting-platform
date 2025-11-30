# Product & Engineering Roadmap – Recruiting SaaS Platform

Phased plan from foundation to ecosystem. Timeframes are intentionally loose to let you pace alongside other work.

## Phase 0 – Foundation (now)
**Goal:** stable skeleton ready for real test data.
- **Product:** register/login; create jobs (manual/prompt/upload); create candidates (manual/resume); match jobs↔candidates with understandable reasons; chat assistant navigation.
- **Engineering:**
  - Dev env polish: `docker compose -f infra/docker-compose.yml up --build`; idempotent seed script (demo org, 3–5 jobs, 10–20 candidates, applications).
  - Validation & errors: job title required; salary consistency; candidate name required; map 4xx/5xx to friendly `st.error`.
  - Observability: structured logging per `/matching/*` (job/candidate IDs + scores) and `/agent/*` (user + intent); simple log view/CLI for match logs.
  - UX smoothing: stable login state; sidebar “Logged in as <email>”; logout button clears session.

## Phase 1 – MVP & Early Users
**Goal:** private beta usable by a solo recruiter.
- **Product:** recruit, add roles, upload resumes, ask “who first for role X,” get ranked list with reasons; onboard a handful of real users.
- **Engineering:**
  - Role-based access: `org_admin`, `recruiter`, `viewer`; enforce perms (org settings, CRUD, read-only).
  - Jobs UI: table with sort/filter; inline edit/close; open in match view.
  - Candidates UI: table with search (name/location/title); detail view (notes, links, applications).
  - Applications/pipeline: show applications on candidate + job detail; update status via dropdown (sourced→hired).
  - Basic analytics: counts for open jobs, active candidates, matches run this week; backend queries + simple charts.
  - Onboarding demo mode: toggle to seed sandbox org for “play” without real data.

## Phase 2 – Premium Features & Scale
**Goal:** differentiated, reliable paid product.
- **Product:** strong matching with explainability; candidate pools/projects; light ATS (jobs, candidates, applications, notes, tasks).
- **Engineering:**
  - Matching 2.0: adjustable weights (title/skills/location); location awareness; required vs. nice-to-have weighting; per-job “match profile tuning.”
  - OpenAI in prod: enable `MATCHING_USE_OPENAI=true`; cache embeddings per job/candidate (hash of normalized text); org-level usage counters for billing/throttling.
  - Candidate pools & tags: tags (e.g., backend, principal, NYC); tag-based search; expose tags in reasons.
  - Tasks & notes: Task entity (id, org_id, owner_user_id, candidate_id?, job_id?, due_at, status, body); simple to-do UI; future agent skill to create tasks.
  - Agent UX: minimal conversation history; new commands (“show senior backend candidates,” “clone job 5 but remote in Austin”).

## Phase 3 – Intelligence & Automation
**Goal:** smart recruiting co-pilot with memory and proactive help.
- **Product:** remembers recruiter preferences; proposes candidates; AI for outreach, summaries, interview prep.
- **Engineering:**
  - Personalization: track recruiter feedback (“good/not a fit/interview”); preference model to reweight scores; recommendation endpoint for new candidates matching taste.
  - Outreach drafting: generate candidate outreach + internal summaries; Streamlit button; org-level templates/tone.
  - Interview questions: job + candidate → suggested questions; optional `InterviewKit` entity.
  - Multi-channel summaries: Slack/Teams-friendly summaries (top candidates for job X).
  - Automation rules v1: notifications on pipeline changes or high-score matches; simple job runner/queue.

## Phase 4 – Platform & Ecosystem
**Goal:** from tool to platform with integrations and extensibility.
- **Engineering:**
  - Public API & keys: ApiKey model (key, org_id, scopes, created_by); support `Authorization: ApiKey <key>`; `PUBLIC_API_REFERENCE.md`.
  - ATS connectors: Greenhouse/Lever sync (jobs/candidates; push match scores); CSV import/export.
  - Webhooks: subscriptions (`candidate.created`, `job.created`, `match.created`, `application.status_changed`); UI for endpoints; signed requests.
  - Plugin/extension system: per-org custom scoring (sandboxed/limited runtime).
  - Marketplace/scorecards: shared scorecard templates (e.g., Senior Backend, ML Engineer, SRE); optional anonymized insights.

## Meta – Process & Tooling
- **Dev workflow:** feature/* branches; PR template (summary, screenshots for UI, testing notes); lint (`ruff`/`flake8`), format (`black`), tests (`pytest`); basic UI tests/snapshots.
- **CI/CD:** GitHub Actions for lint+test on PR; build/push Docker images on merge; main → staging; manual promote to prod.
- **Data & privacy:** publish privacy/terms; org data deletion; log redaction for PII in debug logs.

## Suggested Milestones
- **M1: Walking Skeleton (Phase 0):** compose up; login; create jobs/candidates; run matches; chat works.
- **M2: Usable Solo Recruiter Tool (Phase 1):** pipeline + analytics; a few friendly users live.
- **M3: Sellable MVP (Phase 2):** Matching 2.0; Postgres, SSL, basic observability; charge early adopters.
- **M4: Smart Co-pilot (Phase 3):** personalized, explainable suggestions; outreach/interview helpers.
- **M5: Platform (Phase 4):** integrations, webhooks, public API; potential marketplace/ecosystem.
