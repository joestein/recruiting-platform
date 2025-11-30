# REST API Reference – Recruiting SaaS Platform

Base URLs (dev):
- Backend root: `http://localhost:8000`
- API root: `http://localhost:8000/api/v1`

Authentication: JWT Bearer in `Authorization: Bearer <access_token>`. All endpoints except `/auth/*` and `/healthz` require auth.

## 1. Authentication & User

### Register
- **POST** `/api/v1/auth/register`
- Creates organization + first user.
- Body (JSON):
```json
{
  "email": "founder@example.com",
  "password": "secret123",
  "org_name": "My Recruiting Co"
}
```
`org_name` optional (defaults to "My Organization").
- Response 200:
```json
{
  "id": 1,
  "email": "founder@example.com",
  "full_name": "founder",
  "role": "org_admin",
  "org_id": 1
}
```

### Login
- **POST** `/api/v1/auth/login`
- Returns JWT (OAuth2 password flow).
- Body (form-encoded):
```
username=founder@example.com
password=secret123
```
- Response 200:
```json
{
  "access_token": "...",
  "token_type": "bearer"
}
```
Use in header: `Authorization: Bearer <access_token>`.

### Current User
- **GET** `/api/v1/users/me`
- Headers: `Authorization: Bearer <access_token>`.
- Response 200 same shape as register response.

## 2. Jobs API

- Base: `/api/v1/jobs` (org-scoped).

### List Jobs
- **GET** `/api/v1/jobs`
- Query: `skip` (int, default 0), `limit` (int, default 50, max 100), `status_filter` (`open|on_hold|closed`), `q` (title search).
- Response 200:
```json
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
```

### Create Job
- **POST** `/api/v1/jobs`
- Body (JSON):
```json
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
```
`title` required; others optional.
- Response 201: JobOut (same shape as list item).

### Get Job by ID
- **GET** `/api/v1/jobs/{job_id}`
- Response 200: JobOut. 404 if missing/wrong org.

### Update Job (Partial)
- **PATCH** `/api/v1/jobs/{job_id}`
- Body: any subset of job fields.
- Response 200: updated JobOut.

### Delete Job
- **DELETE** `/api/v1/jobs/{job_id}`
- Response 204.

## 3. Candidates API

- Base: `/api/v1/candidates`

### List Candidates
- **GET** `/api/v1/candidates`
- Query: `skip` (int, default 0), `limit` (int, default 50, max 100), `q` (search by `full_name`).
- Response 200:
```json
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
```

### Create Candidate
- **POST** `/api/v1/candidates`
- Body (JSON):
```json
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
```
- Response 201: CandidateOut (same shape as list item).

### Get Candidate by ID
- **GET** `/api/v1/candidates/{candidate_id}`
- Response 200: CandidateOut. 404 if missing.

### Update Candidate (Partial)
- **PATCH** `/api/v1/candidates/{candidate_id}`
- Body: any subset of candidate fields.
- Response 200: updated CandidateOut.

### Delete Candidate
- **DELETE** `/api/v1/candidates/{candidate_id}`
- Response 204.

## 4. Applications API

- Base: `/api/v1/applications`

### List Applications
- **GET** `/api/v1/applications`
- Query: `skip` (int, default 0), `limit` (int, default 50, max 100), `job_id` (int), `candidate_id` (int).
- Response 200:
```json
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
```

### Create Application
- **POST** `/api/v1/applications`
- Creates application between existing job and candidate.
- Body (JSON):
```json
{
  "job_id": 5,
  "candidate_id": 12,
  "status": "sourced",
  "source": "manual",
  "fit_score": 85
}
```
`status`, `source`, `fit_score` optional (defaults apply).
- Response 201: ApplicationOut.
- Errors: 404 if job/candidate not found in org; 400 if duplicate (job_id, candidate_id).

### Get Application by ID
- **GET** `/api/v1/applications/{application_id}`
- Response 200: ApplicationOut.

### Update Application
- **PATCH** `/api/v1/applications/{application_id}`
- Body: any subset of `status`, `source`, `fit_score`.
- Response 200: updated ApplicationOut.

### Delete Application
- **DELETE** `/api/v1/applications/{application_id}`
- Response 204.

## 5. Matching API

- Base: `/api/v1/matching` (logs into `match_logs`).

### Candidates for Job (Job → Candidates)
- **POST** `/api/v1/matching/candidates_for_job`
- Body (JSON):
```json
{ "job_id": 5, "limit": 20 }
```
`job_id` required; `limit` optional (default 20).
- Response 200:
```json
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
```
- Errors: 404 if job not found.

### Jobs for Candidate (Candidate → Jobs)
- **POST** `/api/v1/matching/jobs_for_candidate`
- Body (JSON):
```json
{ "candidate_id": 12, "limit": 20 }
```
- Response 200:
```json
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
```
- Errors: 404 if candidate not found.

## 6. Agent Chat API

- Base: `/api/v1/agent`

### Chat with Recruiter Agent
- **POST** `/api/v1/agent/chat`
- High-level natural-language interface.
- Body (JSON):
```json
{
  "conversation_id": null,
  "message": "match candidates for job 5",
  "mode": "recruiter_assistant"
}
```
`conversation_id` currently unused; `mode` reserved (default `recruiter_assistant`).
- Response 200:
```json
{
  "reply": "Here are the top candidate matches for job #5:\n\n- Candidate #12: Jane Doe (Staff Engineer @ TechCorp), score=87, strategy=openai. Why: High semantic similarity between job and profile. Overlapping terms include: backend, python, distributed.\n\nYou can now say things like:\n- 'show applications for job 5'\n- 'list candidates' to see everyone."
}
```
- Supported commands (examples): create job from prompt, list jobs/open jobs, list candidates, summarize candidate {id}, match candidates for job {id}, match jobs for candidate {id}, applications/pipeline for job {id}.

## 7. Agent – Job Creation APIs

- Base: `/api/v1/agent/jobs`

### Create Job from Prompt
- **POST** `/api/v1/agent/jobs/from_prompt`
- Body (JSON):
```json
{ "prompt": "We need a Senior Backend Engineer in NYC with Python, FastAPI, and PostgreSQL experience..." }
```
- Response 200:
```json
{
  "raw_prompt": "...",
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
```

### Create Job from Uploaded Job Req
- **POST** `/api/v1/agent/jobs/from_req`
- Multipart form: `job_req` (file), `notes` (optional text).
- Example:
```bash
curl -X POST http://localhost:8000/api/v1/agent/jobs/from_req \
  -H "Authorization: Bearer <token>" \
  -F "job_req=@job_description.txt" \
  -F "notes=This is for our New York office."
```
- Response 200:
```json
{
  "filename": "job_description.txt",
  "job": { "...": "JobOut fields..." },
  "summary": "I've created a new job from the uploaded file 'job_description.txt':\n\n- Job #6: Senior Backend Engineer\n- Location: New York, NY\n- Employment type: Full-time\n- Remote option: Hybrid\n- Salary range: 150000–190000 USD\n- Required skills: Python, FastAPI, PostgreSQL\n\nYou can now say things like:\n- 'match candidates for job 6'\n- 'list jobs' to see it among your openings."
}
```

## 8. Agent – Candidate / Resume APIs

- Base: `/api/v1/agent/candidates`

### Create Candidate from Resume
- **POST** `/api/v1/agent/candidates/from_resume`
- Multipart form: `resume` (file), `notes` (optional text).
- Example:
```bash
curl -X POST http://localhost:8000/api/v1/agent/candidates/from_resume \
  -H "Authorization: Bearer <token)" \
  -F "resume=@jane_doe_resume.pdf" \
  -F "notes=Strong Python + distributed systems background."
```
- Response 200:
```json
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
```

## 9. Health Check

- **GET** `/healthz`
- Response 200:
```json
{ "status": "ok" }
```
Useful for readiness/liveness checks.

## 10. Error Format

Most errors return:
```json
{ "detail": "Error message" }
```
Common statuses: 400 (validation/duplicates), 401 (missing/invalid token), 403 (invalid credentials/token decode), 404 (not found in org), 422 (schema validation).

---
Append new sections as new routers/services are added (e.g., `/experience`, `/webhooks`, `/billing`).
