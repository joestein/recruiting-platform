from __future__ import annotations

import json
from typing import Any, Dict

from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..models.job import Job
from ..models.user import User

settings = get_settings()


def _extract_job_struct_from_prompt_with_openai(prompt: str) -> Dict[str, Any]:
    from openai import OpenAI

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    system_msg = (
        "You are an assistant that extracts structured job descriptions from natural language. "
        "Given a prompt describing a job opening, you MUST respond with a single JSON object ONLY, "
        "with the following keys:\n"
        "  title: string\n"
        "  department: string or null\n"
        "  location: string or null\n"
        "  employment_type: string or null\n"
        "  remote_option: string or null\n"
        "  salary_min: integer or null\n"
        "  salary_max: integer or null\n"
        "  currency: 3-letter code string or null (example: 'USD')\n"
        "  description: string or null\n"
        "  required_skills: array of strings or null\n"
        "  nice_to_have_skills: array of strings or null\n"
        "Do not include any explanation text, only valid JSON."
    )

    resp = client.chat.completions.create(
        model=settings.OPENAI_CHAT_MODEL,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
    )

    content = resp.choices[0].message.content
    data = json.loads(content)
    if not isinstance(data, dict):
        raise ValueError("Model did not return a JSON object")
    return data


def _extract_job_struct_from_prompt(prompt: str) -> Dict[str, Any]:
    if settings.OPENAI_API_KEY:
        try:
            return _extract_job_struct_from_prompt_with_openai(prompt)
        except Exception as e:
            print(f"[agent_jobs] OpenAI extraction failed, falling back to naive. Error: {e}")

    return {
        "title": (prompt[:80] or "Untitled role"),
        "department": None,
        "location": None,
        "employment_type": None,
        "remote_option": None,
        "salary_min": None,
        "salary_max": None,
        "currency": "USD",
        "description": prompt,
        "required_skills": [],
        "nice_to_have_skills": [],
    }


def create_job_from_prompt(
    *,
    db: Session,
    user: User,
    prompt: str,
) -> Job:
    struct = _extract_job_struct_from_prompt(prompt)

    job = Job(
        org_id=user.org_id,
        created_by_user_id=user.id,
        title=struct.get("title") or "Untitled role",
        department=struct.get("department"),
        location=struct.get("location"),
        employment_type=struct.get("employment_type"),
        remote_option=struct.get("remote_option"),
        salary_min=struct.get("salary_min"),
        salary_max=struct.get("salary_max"),
        currency=struct.get("currency") or "USD",
        description=struct.get("description"),
        required_skills=struct.get("required_skills") or [],
        nice_to_have_skills=struct.get("nice_to_have_skills") or [],
        status="open",
        is_public=False,
    )

    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def create_job_from_req(
    *,
    db: Session,
    user: User,
    file_bytes: bytes,
    filename: str,
    extra_notes: str | None = None,
) -> Job:
    text = file_bytes.decode("utf-8", errors="ignore")

    if extra_notes:
        text = text + "\n\nRecruiter notes:\n" + extra_notes

    struct = _extract_job_struct_from_prompt(text)

    job = Job(
        org_id=user.org_id,
        created_by_user_id=user.id,
        title=struct.get("title") or "Untitled role",
        department=struct.get("department"),
        location=struct.get("location"),
        employment_type=struct.get("employment_type"),
        remote_option=struct.get("remote_option"),
        salary_min=struct.get("salary_min"),
        salary_max=struct.get("salary_max"),
        currency=struct.get("currency") or "USD",
        description=struct.get("description") or text,
        required_skills=struct.get("required_skills") or [],
        nice_to_have_skills=struct.get("nice_to_have_skills") or [],
        status="open",
        is_public=False,
    )

    db.add(job)
    db.commit()
    db.refresh(job)
    return job
