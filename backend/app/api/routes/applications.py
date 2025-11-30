from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ...models.application import Application
from ...models.candidate import Candidate
from ...models.job import Job
from ...models.user import User
from ...schemas.applications import (
    ApplicationCreate,
    ApplicationList,
    ApplicationOut,
    ApplicationUpdate,
)
from ..deps import get_current_user, get_db

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("", response_model=ApplicationList)
def list_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = Query(50, le=100),
    job_id: Optional[int] = None,
    candidate_id: Optional[int] = None,
):
    query = db.query(Application).filter(Application.org_id == current_user.org_id)

    if job_id:
        query = query.filter(Application.job_id == job_id)
    if candidate_id:
        query = query.filter(Application.candidate_id == candidate_id)

    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return ApplicationList(items=items, total=total)


@router.post("", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
def create_application(
    payload: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(Job).filter(Job.id == payload.job_id, Job.org_id == current_user.org_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    candidate = (
        db.query(Candidate)
            .filter(Candidate.id == payload.candidate_id, Candidate.org_id == current_user.org_id)
            .first()
    )
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    existing = (
        db.query(Application)
        .filter(
            Application.org_id == current_user.org_id,
            Application.job_id == job.id,
            Application.candidate_id == candidate.id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Application already exists for this candidate and job")

    app = Application(
        org_id=current_user.org_id,
        job_id=job.id,
        candidate_id=candidate.id,
        status=payload.status or "sourced",
        source=payload.source or "manual",
        fit_score=payload.fit_score,
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


@router.get("/{application_id}", response_model=ApplicationOut)
def get_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app = (
        db.query(Application)
        .filter(Application.id == application_id, Application.org_id == current_user.org_id)
        .first()
    )
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


@router.patch("/{application_id}", response_model=ApplicationOut)
def update_application(
    application_id: int,
    payload: ApplicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app = (
        db.query(Application)
        .filter(Application.id == application_id, Application.org_id == current_user.org_id)
        .first()
    )
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(app, key, value)

    db.add(app)
    db.commit()
    db.refresh(app)
    return app


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app = (
        db.query(Application)
        .filter(Application.id == application_id, Application.org_id == current_user.org_id)
        .first()
    )
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    db.delete(app)
    db.commit()
    return
