from __future__ import annotations

import json
from typing import Any, Dict

from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..models.candidate import Candidate
from ..models.user import User

settings = get_settings()


def _extract_candidate_struct_from_resume_with_openai(text: str) -> Dict[str, Any]:
    from openai import OpenAI

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    system_msg = (
        "You are an assistant that extracts structured candidate profiles from resume text. "
        "You MUST respond with a single JSON object ONLY, with keys:\n"
        "  full_name: string\n"
        "  headline: string or null\n"
        "  location: string or null\n"
        "  experience_years: integer or null\n"
        "  current_title: string or null\n"
        "  current_company: string or null\n"
        "  linkedin_url: string or null\n"
        "  github_url: string or null\n"
        "  website_url: string or null\n"
        "  notes: string or null\n"
        "Respond with JSON only. No explanation text."
    )

    resp = client.chat.completions.create(
        model=settings.OPENAI_CHAT_MODEL,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": text},
        ],
        temperature=0.1,
    )

    content = resp.choices[0].message.content
    data = json.loads(content)
    if not isinstance(data, dict):
        raise ValueError("Model did not return a JSON object")
    return data


def _extract_candidate_struct_from_resume(text: str) -> Dict[str, Any]:
    if settings.OPENAI_API_KEY:
        try:
            return _extract_candidate_struct_from_resume_with_openai(text)
        except Exception as e:
            print(f"[agent_candidates] OpenAI extraction failed, falling back to naive. Error: {e}")

    lines = [l.strip() for l in text.splitlines() if l.strip()]
    full_name = lines[0][:120] if lines else "Unknown Candidate"
    notes = "\n".join(lines[:20]) if lines else None

    return {
        "full_name": full_name,
        "headline": None,
        "location": None,
        "experience_years": None,
        "current_title": None,
        "current_company": None,
        "linkedin_url": None,
        "github_url": None,
        "website_url": None,
        "notes": notes,
    }


def create_candidate_from_resume(
    *,
    db: Session,
    user: User,
    file_bytes: bytes,
    filename: str,
    extra_notes: str | None = None,
) -> Candidate:
    text = file_bytes.decode("utf-8", errors="ignore")

    struct = _extract_candidate_struct_from_resume(text)

    notes = struct.get("notes") or ""
    if extra_notes:
        notes = (notes + "\n\n" if notes else "") + f"Additional recruiter notes: {extra_notes}"

    candidate = Candidate(
        org_id=user.org_id,
        user_id=None,
        full_name=struct.get("full_name") or "Unknown Candidate",
        headline=struct.get("headline"),
        location=struct.get("location"),
        experience_years=struct.get("experience_years"),
        current_title=struct.get("current_title"),
        current_company=struct.get("current_company"),
        linkedin_url=struct.get("linkedin_url"),
        github_url=struct.get("github_url"),
        website_url=struct.get("website_url"),
        notes=notes,
    )

    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate
