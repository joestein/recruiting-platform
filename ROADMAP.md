Product & Engineering Roadmap – Recruiting SaaS Platform

This roadmap is organized into:

Phase 0 – Foundation (now)

Phase 1 – MVP & Early Users

Phase 2 – Premium Features & Scale

Phase 3 – Intelligence & Automation

Phase 4 – Platform & Ecosystem

Each phase has:

Product goals

Engineering tasks

Suggested milestones

Timeframes are intentionally loose so you can pace this alongside everything else you’re doing.

Phase 0 – Foundation (NOW)

Goal: Make the current skeleton stable, pleasant to use, and ready for real test data.

Product Goals

A recruiter can:

Register/log in

Create jobs (manual, prompt-based, job-req-upload-based)

Create candidates (manual, resume-upload-based)

Match jobs ↔ candidates and understand why.

Use the chat assistant to quickly navigate data.

Engineering Tasks

0.1 Polish dev environment

 Confirm docker-compose path works cleanly:

docker compose -f infra/docker-compose.yml up --build

 Seed script for demo data:

Demo org, 3–5 jobs, 10–20 candidates, a handful of applications

Make it idempotent

0.2 Validation & Error handling

 Add strong validation on:

Job creation (title required, salary fields consistent if present)

Candidate creation (name required)

 Surface readable errors in Streamlit:

Map 4xx/5xx to st.error("...") with friendly messages

0.3 Basic Observability in Dev

 Add structured logging to backend:

Each /matching/* request logging job/candidate IDs + scores

Each /agent/* call logging user id + intent inferred

 Simple logging view (or CLI script) to inspect match logs

0.4 UX smoothing

 Make sure login state flows nicely between pages (no random logouts).

 Add “You are logged in as <email>” to a Streamlit sidebar on each page.

 Add a simple “Logout” button that clears session.

Phase 1 – MVP & Early Users

Goal: Ship an internal/private beta you could legitimately use as a solo technical recruiter.

Product Goals

MVP user story:

Recruiter signs up.

Adds a few roles (job titles + descriptions).

Uploads a set of resumes.

Asks “Who should I talk to first for role X?”

Gets a prioritized list with reasons they can trust.

Able to onboard a handful of real users or friendly customers.

Engineering Tasks

1.1 Role-based Access & Multi-user

 Extend User.role semantics:

org_admin, recruiter, viewer

 Simple enforcement:

Only org_admin can manage org-level settings

recruiter can CRUD jobs/candidates/applications

viewer is read-only

1.2 Jobs & Candidates UI

 Flesh out Jobs page:

Table of jobs with sort/filter

Inline actions: edit, close job, open in “match” view

 Flesh out Candidates page:

Table of candidates with search by name/location/title

Click-through for candidate detail view (show notes, links, applications)

1.3 Applications / Pipeline UI

 On candidate detail page:

Show their applications & status

 On job detail page:

Simple pipeline view (list all applications to that job)

 Allow updating application status from UI (dropdown: sourced → applied → screen → interview → offer → hired)

1.4 Basic Analytics

 Simple metrics view:

Number of jobs open

Number of active candidates

Number of matches run this week

 Build underlying queries in backend; front-end charts can be very minimal.

1.5 Onboarding demo mode

 “Demo data” toggle:

If enabled, seed a sandbox org and allow “Play with demo org” without requiring real data.

 Useful for demos and quick product tours.

Phase 2 – Premium Features & Scale

Goal: Turn MVP into something paid users would actually stick with. Focus on differentiation & reliability.

Product Goals

Solid matching quality with explainability.

Better management of candidate pools and projects.

Early steps toward a “light ATS”: jobs, candidates, applications, notes, tasks.

Engineering Tasks

2.1 Matching 2.0

 Weighting model:

Let user adjust weights: title match vs. skills vs. location.

 Add location-awareness:

Penalize distance if job is on-site and candidate is far away.

 Add “required vs nice-to-have” weights:

Hard requirements heavily penalize if missing.

 Add “match profile tuning”:

For a job, allow user to specify:

“I care more about X than Y”

Save as match settings for that role.

2.2 OpenAI Matching in Production

 Turn on MATCHING_USE_OPENAI=true for staging / prod.

 Add safe fallbacks & caching:

Cache embeddings per job & candidate

Use hash of normalized text as key

 Add usage counters by organization:

For future billing & throttling

2.3 Candidate Pools & Tags

 Add tags for candidates:

["backend", "principal", "NYC", "ex-FAANG"]

 Simple pooling:

DSL: “Pool: Senior Backend NYC”

Tag-based search in front-end

 Expose tags in matching reason:

“Matches this job’s keywords and is in pool ‘backend-nyc’”

2.4 Tasks & Notes

 Add Task entity:

id, org_id, owner_user_id, candidate_id?, job_id?, due_at, status, body

 Simple UI:

“To-do” list of follow-ups

Task creation from chat (“create a follow-up for candidate 7 next week” can be a future agent skill)

2.5 Improved Agent UX

 Multi-turn context (phase 2.5+):

Minimal conversation history stored in DB keyed by user + conversation.

 Add more natural commands:

“Show me all senior backend candidates we have.”

“Create a job like job 5 but remote in Austin.”

Phase 3 – Intelligence & Automation

Goal: Start feeling like a truly smart technical recruiting co-pilot, not just a UI over CRUD+matching.

Product Goals

Recruiters feel the system “knows their taste.”

System starts to remember preferences and proactively propose candidates.

AI helps with outreach, summaries, and interview prep.

Engineering Tasks

3.1 Personalization

 Track which candidate-job matches the recruiter marks as:

“good”, “not a fit”, “interview”, etc.

 Feed this into a simple “preference model”:

Reweight scores for that recruiter/org

 Recommendation endpoint:

“show me newly-added candidates that match my typical backend hiring taste”

3.2 Outbound Email Drafting (optional)

 Add endpoints for generating:

Outreach emails to candidates

Internal recommendation summaries (Slack-ready)

 Streamlit UI:

Button: “Generate outreach email” from candidate+job pair.

 Support templates per org:

Configurable tone (formal vs casual, etc.)

3.3 Interview Question Suggestions

 Given job + candidate:

Generate a set of targeted interview questions

 Option to save as InterviewKit entity.

3.4 Multi-channel Summaries

 Slack/Teams summary generator:

“Summarize top 5 candidates for job X as a Slack message.”

 Export as text/Markdown.

3.5 Automation Rules (v1)

 “When a candidate gets to stage screen, send me a daily summary.”

 “If a new candidate matches job 5 with score >85, notify me.”

At this phase, you can start thinking about notifications (Slack, email) with a simple job runner or queue.

Phase 4 – Platform & Ecosystem

Goal: From “tool” to “platform” – extensible, integratable, and possibly marketplace-enabled.

Product Goals

Integrate with existing ATS/HRIS systems.

Provide APIs / webhooks so other tools can build on your matching & AI workflows.

Potentially open “plugins” for custom scoring, data enrichments, etc.

Engineering Tasks

4.1 Public API & API Keys

 Add ApiKey model:

key, org_id, scopes, created_by

 Extend auth:

Allow Authorization: ApiKey <key> for some endpoints.

 Public API docs:

PUBLIC_API_REFERENCE.md

4.2 ATS Connectors

 Greenhouse integration:

Sync jobs and candidates

Push match scores back as custom fields/notes

 Lever integration:

Similar pattern

 Generic CSV import/export flows.

4.3 Webhooks

 Webhook subscriptions:

candidate.created, job.created, match.created, application.status_changed

 UI for managing webhook endpoints.

 Signed webhook requests.

4.4 Plugin / Extension System (advanced)

 Allow per-org custom scoring functions:

Example: user uploads a small Python scoring snippet or config.

 Guard-rail with sandboxing & runtime limits.

4.5 Marketplace / Shared Scorecards

 “Scorecard templates” for common roles:

“Senior Backend Engineer”

“ML Engineer”

“SRE”

 Allow orgs to share (opt-in) aggregated, anonymized insights.

Meta – Process & Tooling

How you actually drive this roadmap forward.

A. Development Workflow

 Standardize on:

feature/* branches

PRs with:

Summary

Screenshots for UI changes

Testing notes

 Code quality:

ruff or flake8 for lint

black for formatting

pytest for backend unit tests

 For front-end:

Basic UI tests / snapshots where possible

B. CI/CD

 GitHub Actions:

Lint + test on PR

Build & push Docker images on merge to main

 Deployment pipeline:

main → staging environment

manual promotion to production

C. Data & Privacy

 Privacy policy and terms (even for friends/beta users)

 Option to delete all data for an org

 Log redaction for PII in debug logs

Suggested Milestone Breakdown

Milestone 1 – “Walking Skeleton” (Phase 0)

Runs with Docker Compose

You can log in, create jobs & candidates, run matches, and use chat.

Milestone 2 – “Usable Solo Recruiter Tool” (Phase 1)

Usable pipeline & analytics

Two or three friendly users running small roles through it.

Milestone 3 – “Sellable MVP” (Phase 2)

Matching 2.0

Reliable Postgres, SSL, and basic observability

You’d feel okay charging early adopters.

Milestone 4 – “Smart Co-pilot” (Phase 3)

Personalized, explainable suggestions

Outreach & interview helper flows.

Milestone 5 – “Platform” (Phase 4)

Integrations, webhooks, public API

Potential app marketplace & ecosystem.