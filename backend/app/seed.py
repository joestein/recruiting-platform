from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from sqlalchemy.orm import Session

from .core.database import SessionLocal
from .models.job import Job
from .models.organization import Organization
from .models.user import User
from .core.security import get_password_hash


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text()) or {}


def seed_demo_data(seed_path: str, demo_password_override: Optional[str] = None) -> None:
    """
    Seed a demo org, user, and a single job from YAML.
    Idempotent: matches on org.slug and job.title within that org.
    """
    path = Path(seed_path)
    data = _load_yaml(path)
    if not data:
        return

    org_data = data.get("organization") or {}
    user_data = data.get("user") or {}
    job_data = data.get("job") or {}
    if not org_data or not user_data or not job_data:
        return

    session: Session = SessionLocal()
    try:
        org = session.query(Organization).filter(Organization.slug == org_data.get("slug")).first()
        if not org:
            org = Organization(
                name=org_data.get("name", "Demo Org"),
                slug=org_data.get("slug", "demo"),
                plan=org_data.get("plan", "free"),
            )
            session.add(org)
            session.commit()
            session.refresh(org)

        user = session.query(User).filter(User.email == user_data.get("email")).first()
        if not user:
            password_plain = demo_password_override or user_data.get("password") or "changeme123"
            user = User(
                email=user_data.get("email", "demo@example.com"),
                full_name=user_data.get("full_name", "Demo Admin"),
                org_id=org.id,
                role=user_data.get("role", "org_admin"),
                hashed_password=get_password_hash(password_plain),
            )
            session.add(user)
            session.commit()
            session.refresh(user)

        existing_job = (
            session.query(Job)
            .filter(Job.org_id == org.id)
            .filter(Job.title == job_data.get("title"))
            .first()
        )
        if not existing_job:
            job = Job(
                org_id=org.id,
                created_by_user_id=user.id,
                title=job_data.get("title"),
                department=job_data.get("department"),
                location=job_data.get("location"),
                employment_type=job_data.get("employment_type"),
                remote_option=job_data.get("remote_option"),
                salary_min=job_data.get("salary_min"),
                salary_max=job_data.get("salary_max"),
                currency=job_data.get("currency"),
                description=job_data.get("description"),
                required_skills=job_data.get("required_skills"),
                nice_to_have_skills=job_data.get("nice_to_have_skills"),
                status=job_data.get("status", "open"),
                is_public=job_data.get("is_public", False),
            )
            session.add(job)
            session.commit()
    finally:
        session.close()
