from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from ..models.application import Application
from ..models.candidate import Candidate
from ..models.job import Job
from ..models.user import User
from .agent_jobs import create_job_from_prompt
from .matching import (
    CandidateMatch,
    JobMatch,
    rank_candidates_for_job,
    rank_jobs_for_candidate,
)


def _format_jobs(jobs: List[Job]) -> str:
    if not jobs:
        return "I don't see any jobs yet for your organization."
    lines = []
    for j in jobs[:10]:
        lines.append(
            f"- [Job #{j.id}] {j.title} — {j.location or 'location N/A'} "
            f"({j.status}, {j.employment_type or 'type N/A'})"
        )
    if len(jobs) > 10:
        lines.append(f"...and {len(jobs) - 10} more.")
    return "\n".join(lines)


def _format_candidates(candidates: List[Candidate]) -> str:
    if not candidates:
        return "I don't see any candidates yet for your organization."
    lines = []
    for c in candidates[:10]:
        lines.append(
            f"- [Candidate #{c.id}] {c.full_name} — "
            f"{c.current_title or 'title N/A'} @ {c.current_company or 'company N/A'}"
        )
    if len(candidates) > 10:
        lines.append(f"...and {len(candidates) - 10} more.")
    return "\n".join(lines)


def _format_applications(apps: List[Application]) -> str:
    if not apps:
        return "No applications found for that filter."
    lines = []
    for a in apps[:15]:
        lines.append(
            f"- Application #{a.id}: candidate #{a.candidate_id} on job #{a.job_id} "
            f"status={a.status}, fit_score={a.fit_score or 'N/A'}"
        )
    if len(apps) > 15:
        lines.append(f"...and {len(apps) - 15} more.")
    return "\n".join(lines)


def _format_candidate_matches(matches: list[CandidateMatch]) -> str:
    if not matches:
        return "I couldn't find any good matches for that job."

    lines = []
    for m in matches[:15]:
        c = m.candidate
        reason_snippet = m.reason or "No detailed reason available."
        lines.append(
            f"- Candidate #{c.id}: {c.full_name} "
            f"({c.current_title or 'title N/A'} @ {c.current_company or 'company N/A'}), "
            f"score={m.score}, strategy={m.strategy}. "
            f"Why: {reason_snippet}"
        )
    if len(matches) > 15:
        lines.append(f"...and {len(matches) - 15} more lower-scoring matches.")
    return "\n".join(lines)


def _format_job_matches(matches: list[JobMatch]) -> str:
    if not matches:
        return "I couldn't find any good job matches for that candidate."

    lines = []
    for m in matches[:15]:
        j = m.job
        reason_snippet = m.reason or "No detailed reason available."
        lines.append(
            f"- Job #{j.id}: {j.title} "
            f"({j.location or 'location N/A'}, status={j.status}), "
            f"score={m.score}, strategy={m.strategy}. "
            f"Why: {reason_snippet}"
        )
    if len(matches) > 15:
        lines.append(f"...and {len(matches) - 15} more lower-scoring matches.")
    return "\n".join(lines)


def _summarize_candidate(c: Candidate) -> str:
    bits = [f"Candidate #{c.id}: {c.full_name}."]
    if c.current_title:
        bits.append(f" Current title: {c.current_title}.")
    if c.current_company:
        bits.append(f" Current company: {c.current_company}.")
    if c.location:
        bits.append(f" Location: {c.location}.")
    if c.headline:
        bits.append(f" Headline: {c.headline}.")
    if c.notes:
        snippet = c.notes[:280] + ("..." if len(c.notes) > 280 else "")
        bits.append(f" Notes snippet: {snippet}")
    return " ".join(bits)


def run_agent_chat(
    *,
    db: Session,
    user: User,
    message: str,
    mode: str = "recruiter_assistant",
) -> str:
    text = message.strip()
    lower = text.lower()
    org_id = user.org_id

    # New job creation from prompt
    if (
        "create a new job" in lower
        or lower.startswith("new job")
        or "open a role" in lower
        or lower.startswith("create job")
    ):
        job = create_job_from_prompt(db=db, user=user, prompt=message)
        skills = job.required_skills or []
        skills_str = ", ".join(skills) if skills else "N/A"

        return (
            f"I've created a new job in your org:\n\n"
            f"- Job #{job.id}: {job.title}\n"
            f"- Location: {job.location or 'N/A'}\n"
            f"- Employment type: {job.employment_type or 'N/A'}\n"
            f"- Remote option: {job.remote_option or 'N/A'}\n"
            f"- Salary range: "
            f"{job.salary_min if job.salary_min is not None else 'N/A'}–"
            f"{job.salary_max if job.salary_max is not None else 'N/A'} "
            f"{job.currency or 'N/A'}\n"
            f"- Required skills: {skills_str}\n\n"
            f"You can now say things like:\n"
            f"- 'match candidates for job {job.id}'\n"
            f"- 'show applications for job {job.id}'\n"
            f"- 'list jobs' to see it in your job list."
        )

    # Summarize candidate
    if (
        "summarize candidate" in lower
        or "who is candidate" in lower
        or "tell me about candidate" in lower
    ):
        cand_id = None
        tokens = lower.replace("#", "").split()
        for i, t in enumerate(tokens):
            if t == "candidate" and i + 1 < len(tokens):
                try:
                    cand_id = int(tokens[i + 1])
                    break
                except ValueError:
                    continue

        if cand_id is None:
            return (
                "I can summarize a candidate if you say something like "
                "'summarize candidate 12' or 'who is candidate #5'. I couldn't detect a candidate id."
            )

        cand = (
            db.query(Candidate)
            .filter(Candidate.org_id == org_id, Candidate.id == cand_id)
            .first()
        )
        if not cand:
            return f"I couldn't find candidate #{cand_id} in your organization."

        summary = _summarize_candidate(cand)
        return (
            summary
            + f"\n\nYou can now ask me to match them to jobs, e.g. 'match jobs for candidate {cand_id}', "
              "or view their profile in the Candidates page."
        )

    # Match candidates for job
    if (
        "candidates for job" in lower
        or "match candidates for job" in lower
        or "best candidates for job" in lower
    ):
        job_id = None
        tokens = lower.replace("#", "").split()
        for i, t in enumerate(tokens):
            if t == "job" and i + 1 < len(tokens):
                try:
                    job_id = int(tokens[i + 1])
                    break
                except ValueError:
                    continue

        if job_id is None:
            return (
                "To match candidates, say something like "
                "'match candidates for job 5' or 'show best candidates for job 12'. "
                "I couldn't detect a job id in your message."
            )

        try:
            matches = rank_candidates_for_job(
                db=db,
                org_id=org_id,
                job_id=job_id,
                limit=20,
            )
        except ValueError:
            return f"I couldn't find job #{job_id} in your organization."

        body = _format_candidate_matches(matches)
        return (
            f"Here are the top candidate matches for job #{job_id}:\n\n{body}\n\n"
            f"You can now say things like:\n"
            f"- 'show applications for job {job_id}'\n"
            f"- 'list candidates' to see everyone."
        )

    # Match jobs for candidate
    if "jobs for candidate" in lower or "match jobs for candidate" in lower:
        cand_id = None
        tokens = lower.replace("#", "").split()
        for i, t in enumerate(tokens):
            if t == "candidate" and i + 1 < len(tokens):
                try:
                    cand_id = int(tokens[i + 1])
                    break
                except ValueError:
                    continue

        if cand_id is None:
            return (
                "To match jobs, say something like "
                "'match jobs for candidate 5' or 'find jobs for candidate #12'. "
                "I couldn't detect a candidate id in your message."
            )

        try:
            matches = rank_jobs_for_candidate(
                db=db,
                org_id=org_id,
                candidate_id=cand_id,
                limit=20,
            )
        except ValueError:
            return f"I couldn't find candidate #{cand_id} in your organization."

        body = _format_job_matches(matches)
        return (
            f"Here are the top job matches for candidate #{cand_id}:\n\n{body}\n\n"
            f"You can now say things like:\n"
            f"- 'match candidates for job <id>' for any of these jobs."
        )

    # List jobs
    if any(word in lower for word in ["list jobs", "show jobs", "open roles", "open jobs"]):
        jobs = db.query(Job).filter(Job.org_id == org_id).order_by(Job.created_at.desc()).all()
        body = _format_jobs(jobs)
        return (
            f"Here are some jobs I see for your org:\n\n{body}\n\n"
            "You can ask me things like:\n- 'Show only open jobs'\n- 'List jobs with backend in the title'"
        )

    if "jobs" in lower and "open" in lower:
        jobs = (
            db.query(Job)
            .filter(Job.org_id == org_id, Job.status == "open")
            .order_by(Job.created_at.desc())
            .all()
        )
        body = _format_jobs(jobs)
        return f"Here are your open jobs:\n\n{body}"

    # List candidates
    if any(word in lower for word in ["list candidates", "show candidates", "my candidates"]):
        candidates = (
            db.query(Candidate)
            .filter(Candidate.org_id == org_id)
            .order_by(Candidate.created_at.desc())
            .all()
        )
        body = _format_candidates(candidates)
        return (
            f"Here are some candidates in your org:\n\n{body}\n\n"
            "You can ask things like:\n- 'Show senior candidates'\n- 'Show candidates in New York'"
        )

    # Applications for job
    if "applications for job" in lower or "pipeline for job" in lower:
        job_id = None
        tokens = lower.replace("#", "").split()
        for i, t in enumerate(tokens):
            if t == "job" and i + 1 < len(tokens):
                try:
                    job_id = int(tokens[i + 1])
                    break
                except ValueError:
                    continue
        if job_id is None:
            return (
                "I can show you the pipeline for a given job, e.g. "
                "'show applications for job 12'. I didn't detect a job id in your message."
            )

        apps = (
            db.query(Application)
            .filter(Application.org_id == org_id, Application.job_id == job_id)
            .order_by(Application.created_at.desc())
            .all()
        )
        body = _format_applications(apps)
        return f"Here are applications for job #{job_id}:\n\n{body}"

    # Default help
    return (
        "I'm your recruiting assistant. I can help with things like:\n\n"
        "- 'Create a new job for a Senior Backend Engineer in NYC...'\n"
        "- 'List jobs'\n"
        "- 'Show open jobs'\n"
        "- 'List candidates'\n"
        "- 'Summarize candidate 3'\n"
        "- 'Match candidates for job 5'\n"
        "- 'Match jobs for candidate 7'\n\n"
        f"You said: '{message}'. Try asking in one of these forms."
    )
