REST API Reference – Recruiting SaaS Platform

Base URL (dev):

Backend root: http://localhost:8000

API root: http://localhost:8000/api/v1

Authentication:

JWT Bearer token in Authorization header
Authorization: Bearer <access_token>

Almost all endpoints (except /auth/* and /healthz) require authentication.

1. Authentication & User
1.1 Register

POST /api/v1/auth/register

Create a new organization and the first user for that org.

Request body (JSON)
{
  "email": "founder@example.com",
  "password": "secret123",
  "org_name": "My Recruiting Co"
}


org_name is optional (defaults to "My Organization").

Response 200 OK
{
  "id": 1,
  "email": "founder@example.com",
  "full_name": "founder",
  "role": "org_admin",
  "org_id": 1
}

1.2 Login

POST /api/v1/auth/login

Returns a JWT access token (OAuth2 password flow).

This endpoint expects form-encoded data (not JSON).

Request (form-data / x-www-form-urlencoded)
username=founder@example.com
password=secret123

Response 200 OK
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}


Use this access_token as:

Authorization: Bearer <access_token>

1.3 Current User

GET /api/v1/users/me

Get the currently authenticated user.

Headers
Authorization: Bearer <access_token>

Response 200 OK
{
  "id": 1,
  "email": "founder@example.com",
  "full_name": "founder",
  "role": "org_admin",
  "org_id": 1
}

2. Jobs API

Base path: /api/v1/jobs

All job records are scoped by org_id of the current user.

2.1 List Jobs

GET /api/v1/jobs

Query params

skip (int, default 0) – offset for pagination

limit (int, default 50, max 100)

status_filter (string, optional): e.g. "open", "on_hold", "closed"

q (string, optional): substring search on job title

Response 200 OK
{
  "items": [
    {
      "id": 5,
      "org_id": 1,
      "created_by_user_id": 1,
      "title": "Senior Backend Engineer",
      "department": "Engineering",
      "location": "New York, NY",
      "employment_type": "Full-time",
      "remote_option": "Hybrid",
      "salary_min": 160000,
      "salary_max": 200000,
      "currency": "USD",
      "description": "We are hiring...",
      "required_skills": ["Python", "FastAPI", "PostgreSQL"],
      "nice_to_have_skills": ["Kubernetes", "AWS"],
      "status": "open",
      "is_public": false
    }
  ],
  "total": 1
}

2.2 Create Job

POST /api/v1/jobs

Request body (JSON)
{
  "title": "Senior Backend Engineer",
  "department": "Engineering",
  "location": "New York, NY",
  "employment_type": "Full-time",
  "remote_option": "Hybrid",
  "salary_min": 160000,
  "salary_max": 200000,
  "currency": "USD",
  "description": "We are hiring...",
  "required_skills": ["Python", "FastAPI", "PostgreSQL"],
  "nice_to_have_skills": ["Kubernetes", "AWS"],
  "status": "open",
  "is_public": false
}


title is required; other fields optional.

Response 201 Created

Returns a JobOut:

{
  "id": 5,
  "org_id": 1,
  "created_by_user_id": 1,
  "title": "Senior Backend Engineer",
  "department": "Engineering",
  "location": "New York, NY",
  "employment_type": "Full-time",
  "remote_option": "Hybrid",
  "salary_min": 160000,
  "salary_max": 200000,
  "currency": "USD",
  "description": "We are hiring...",
  "required_skills": ["Python", "FastAPI", "PostgreSQL"],
  "nice_to_have_skills": ["Kubernetes", "AWS"],
  "status": "open",
  "is_public": false
}

2.3 Get Job by ID

GET /api/v1/jobs/{job_id}

Path params

job_id (int)

Response 200 OK

Same shape as JobOut above.

Error 404 Not Found

If job doesn’t exist or doesn’t belong to current org.

2.4 Update Job (Partial)

PATCH /api/v1/jobs/{job_id}

Request body (JSON)

Any subset of fields from:

{
  "title": "Updated title",
  "department": "New Dept",
  "location": "Remote",
  "employment_type": "Contract",
  "remote_option": "Remote",
  "salary_min": 100000,
  "salary_max": 150000,
  "currency": "USD",
  "description": "Updated description",
  "required_skills": ["Python", "Kafka"],
  "nice_to_have_skills": ["Kubernetes"],
  "status": "on_hold",
  "is_public": true
}

Response 200 OK

Updated JobOut.

2.5 Delete Job

DELETE /api/v1/jobs/{job_id}

Response 204 No Content
3. Candidates API

Base path: /api/v1/candidates

3.1 List Candidates

GET /api/v1/candidates

Query params

skip (int, default 0)

limit (int, default 50, max 100)

q (string, optional): search by full_name

Response 200 OK
{
  "items": [
    {
      "id": 12,
      "org_id": 1,
      "full_name": "Jane Doe",
      "headline": "Senior Backend Engineer",
      "location": "San Francisco, CA",
      "experience_years": 8,
      "current_title": "Staff Engineer",
      "current_company": "TechCorp",
      "linkedin_url": "https://linkedin.com/in/janedoe",
      "github_url": "https://github.com/janedoe",
      "website_url": null,
      "notes": "Internal-only notes / extracted resume details."
    }
  ],
  "total": 1
}

3.2 Create Candidate

POST /api/v1/candidates

Request body (JSON)
{
  "full_name": "Jane Doe",
  "headline": "Senior Backend Engineer",
  "location": "San Francisco, CA",
  "experience_years": 8,
  "current_title": "Staff Engineer",
  "current_company": "TechCorp",
  "linkedin_url": "https://linkedin.com/in/janedoe",
  "github_url": "https://github.com/janedoe",
  "website_url": null,
  "notes": "Strong experience with Python and distributed systems."
}

Response 201 Created

CandidateOut:

{
  "id": 12,
  "org_id": 1,
  "full_name": "Jane Doe",
  "headline": "Senior Backend Engineer",
  "location": "San Francisco, CA",
  "experience_years": 8,
  "current_title": "Staff Engineer",
  "current_company": "TechCorp",
  "linkedin_url": "https://linkedin.com/in/janedoe",
  "github_url": "https://github.com/janedoe",
  "website_url": null,
  "notes": "Strong experience with Python and distributed systems."
}

3.3 Get Candidate by ID

GET /api/v1/candidates/{candidate_id}

Response 200 OK

CandidateOut as above.

Error 404 Not Found
3.4 Update Candidate (Partial)

PATCH /api/v1/candidates/{candidate_id}

Request body (JSON)

Any subset of:

{
  "full_name": "Jane Doe",
  "headline": "Principal Engineer",
  "location": "Remote",
  "experience_years": 10,
  "current_title": "Principal Engineer",
  "current_company": "NewCorp",
  "linkedin_url": "https://linkedin.com/in/janedoe",
  "github_url": "https://github.com/janedoe",
  "website_url": "https://janedoe.dev",
  "notes": "Promoted to Principal; leading platform team."
}

Response 200 OK

Updated CandidateOut.

3.5 Delete Candidate

DELETE /api/v1/candidates/{candidate_id}

Response 204 No Content
4. Applications API

Base path: /api/v1/applications

4.1 List Applications

GET /api/v1/applications

Query params

skip (int, default 0)

limit (int, default 50, max 100)

job_id (int, optional)

candidate_id (int, optional)

Response 200 OK
{
  "items": [
    {
      "id": 1,
      "org_id": 1,
      "job_id": 5,
      "candidate_id": 12,
      "status": "sourced",
      "source": "manual",
      "fit_score": 85
    }
  ],
  "total": 1
}

4.2 Create Application

POST /api/v1/applications

Creates an application between an existing job and candidate.

Request body (JSON)
{
  "job_id": 5,
  "candidate_id": 12,
  "status": "sourced",
  "source": "manual",
  "fit_score": 85
}


status, source, fit_score are optional (with defaults).

Response 201 Created
{
  "id": 1,
  "org_id": 1,
  "job_id": 5,
  "candidate_id": 12,
  "status": "sourced",
  "source": "manual",
  "fit_score": 85
}

Errors

404 if job or candidate not found in current org.

400 if an application already exists for that (job_id, candidate_id) pair.

4.3 Get Application by ID

GET /api/v1/applications/{application_id}

Response 200 OK

ApplicationOut.

4.4 Update Application

PATCH /api/v1/applications/{application_id}

Request body (JSON)

Any subset of:

{
  "status": "screening",
  "source": "referral",
  "fit_score": 90
}

Response 200 OK

Updated ApplicationOut.

4.5 Delete Application

DELETE /api/v1/applications/{application_id}

Response 204 No Content
5. Matching API

Base path: /api/v1/matching

These endpoints compute scores and reasons for matches, and log them into match_logs.

5.1 Candidates for Job (Job → Candidates)

POST /api/v1/matching/candidates_for_job

Request body (JSON)
{
  "job_id": 5,
  "limit": 20
}


job_id (required)

limit (optional, default 20)

Response 200 OK
{
  "job_id": 5,
  "matches": [
    {
      "candidate_id": 12,
      "full_name": "Jane Doe",
      "current_title": "Staff Engineer",
      "current_company": "TechCorp",
      "location": "San Francisco, CA",
      "score": 87,
      "reason": "High semantic similarity between job and profile. Overlapping terms include: backend, python, distributed.",
      "strategy": "openai"
    },
    {
      "candidate_id": 13,
      "full_name": "John Smith",
      "current_title": "Senior Backend Engineer",
      "current_company": "OtherCo",
      "location": "Remote",
      "score": 74,
      "reason": "Keyword overlap on: backend, python.",
      "strategy": "naive"
    }
  ]
}


score: integer 0–100

strategy: "openai" or "naive"

Errors

404 if job not found.

5.2 Jobs for Candidate (Candidate → Jobs)

POST /api/v1/matching/jobs_for_candidate

Request body (JSON)
{
  "candidate_id": 12,
  "limit": 20
}

Response 200 OK
{
  "candidate_id": 12,
  "matches": [
    {
      "job_id": 5,
      "title": "Senior Backend Engineer",
      "location": "New York, NY",
      "status": "open",
      "score": 92,
      "reason": "High semantic similarity between candidate and job. Overlapping terms include: backend, python.",
      "strategy": "openai"
    }
  ]
}

Errors

404 if candidate not found.

6. Agent Chat API

Base path: /api/v1/agent

6.1 Chat with Recruiter Agent

POST /api/v1/agent/chat

High-level natural-language interface for recruiters.

Request body (JSON)
{
  "conversation_id": null,
  "message": "match candidates for job 5",
  "mode": "recruiter_assistant"
}


conversation_id currently unused (placeholder for future multi-turn).

message: free-form text.

mode: reserved for future; default "recruiter_assistant".

Response 200 OK
{
  "reply": "Here are the top candidate matches for job #5:\n\n- Candidate #12: Jane Doe (Staff Engineer @ TechCorp), score=87, strategy=openai. Why: High semantic similarity between job and profile. Overlapping terms include: backend, python, distributed.\n\nYou can now say things like:\n- 'show applications for job 5'\n- 'list candidates' to see everyone."
}


The agent supports commands like:

"create a new job for a senior backend engineer in NYC..."

"list jobs" / "show open jobs"

"list candidates"

"summarize candidate 3"

"match candidates for job 5"

"match jobs for candidate 7"

"applications for job 5" / "pipeline for job 5"

7. Agent – Job Creation APIs

Base path: /api/v1/agent/jobs

7.1 Create Job from Prompt

POST /api/v1/agent/jobs/from_prompt

Takes a natural language description; optionally uses OpenAI to structure it.

Request body (JSON)
{
  "prompt": "We need a Senior Backend Engineer in NYC with Python, FastAPI, and PostgreSQL experience..."
}

Response 200 OK
{
  "raw_prompt": "We need a Senior Backend Engineer in NYC with Python, FastAPI, and PostgreSQL experience...",
  "job": {
    "id": 5,
    "org_id": 1,
    "created_by_user_id": 1,
    "title": "Senior Backend Engineer",
    "department": "Engineering",
    "location": "New York, NY",
    "employment_type": "Full-time",
    "remote_option": "Hybrid",
    "salary_min": 160000,
    "salary_max": 200000,
    "currency": "USD",
    "description": "Full job description text...",
    "required_skills": ["Python", "FastAPI", "PostgreSQL"],
    "nice_to_have_skills": ["Kubernetes", "AWS"],
    "status": "open",
    "is_public": false
  }
}

7.2 Create Job from Uploaded Job Req

POST /api/v1/agent/jobs/from_req

Multipart endpoint, used by Streamlit chat sidebar.

Request (multipart/form-data)

job_req: file (job description / job req; currently treated as text)

notes (optional): extra recruiter notes text

Example (conceptual):

curl -X POST http://localhost:8000/api/v1/agent/jobs/from_req \
  -H "Authorization: Bearer <token>" \
  -F "job_req=@job_description.txt" \
  -F "notes=This is for our New York office."

Response 200 OK
{
  "filename": "job_description.txt",
  "job": {
    "id": 6,
    "org_id": 1,
    "created_by_user_id": 1,
    "title": "Senior Backend Engineer",
    "department": "Engineering",
    "location": "New York, NY",
    "employment_type": "Full-time",
    "remote_option": "Hybrid",
    "salary_min": 150000,
    "salary_max": 190000,
    "currency": "USD",
    "description": "Parsed from file...",
    "required_skills": ["Python", "FastAPI", "PostgreSQL"],
    "nice_to_have_skills": [],
    "status": "open",
    "is_public": false
  },
  "summary": "I've created a new job from the uploaded file 'job_description.txt':\n\n- Job #6: Senior Backend Engineer\n- Location: New York, NY\n- Employment type: Full-time\n- Remote option: Hybrid\n- Salary range: 150000–190000 USD\n- Required skills: Python, FastAPI, PostgreSQL\n\nYou can now say things like:\n- 'match candidates for job 6'\n- 'list jobs' to see it among your openings."
}

8. Agent – Candidate / Resume APIs

Base path: /api/v1/agent/candidates

8.1 Create Candidate from Resume

POST /api/v1/agent/candidates/from_resume

Multipart endpoint for creating a candidate record from an uploaded resume.

Request (multipart/form-data)

resume: file (PDF/DOC/TXT etc.; currently treated as text)

notes (optional): additional recruiter notes

Example:

curl -X POST http://localhost:8000/api/v1/agent/candidates/from_resume \
  -H "Authorization: Bearer <token>" \
  -F "resume=@jane_doe_resume.pdf" \
  -F "notes=Strong Python + distributed systems background."

Response 200 OK
{
  "candidate": {
    "id": 12,
    "org_id": 1,
    "full_name": "Jane Doe",
    "headline": "Senior Backend Engineer",
    "location": "San Francisco, CA",
    "experience_years": 8,
    "current_title": "Staff Engineer",
    "current_company": "TechCorp",
    "linkedin_url": "https://linkedin.com/in/janedoe",
    "github_url": "https://github.com/janedoe",
    "website_url": null,
    "notes": "Extracted notes from resume...\n\nAdditional recruiter notes: Strong Python + distributed systems background."
  },
  "summary": "Created candidate #12: Jane Doe. Current title: Staff Engineer. Current company: TechCorp. Location: San Francisco, CA. Headline: Senior Backend Engineer."
}

9. Health Check

GET /healthz

Response 200 OK
{
  "status": "ok"
}


Useful for readiness/liveness checks.

10. Error Format

Most errors return:

{
  "detail": "Error message"
}


Common statuses:

400 Bad Request – validation issues, duplicates, etc.

401 Unauthorized – missing/invalid token (via auth scheme)

403 Forbidden – invalid credentials / token decode issues

404 Not Found – resource not found for current org

422 Unprocessable Entity – schema validation errors (FastAPI default)

This reference covers all current endpoints for your platform.
As you add new routers and services, you can append new sections here (e.g., /experience, /webhooks, /billing, etc.).