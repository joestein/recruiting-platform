from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ...models.job import Job
from ...models.user import User
from ...schemas.jobs import JobCreate, JobList, JobOut, JobUpdate
from ..deps import get_current_user, get_db

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=JobList)
def list_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = Query(50, le=100),
    status_filter: Optional[str] = None,
    q: Optional[str] = None,
):
    query = db.query(Job).filter(Job.org_id == current_user.org_id)

    if status_filter:
        query = query.filter(Job.status == status_filter)

    if q:
        like = f"%{q}%"
        query = query.filter(Job.title.ilike(like))

    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return JobList(items=items, total=total)


@router.post("", response_model=JobOut, status_code=status.HTTP_201_CREATED)
def create_job(
    payload: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = Job(
        org_id=current_user.org_id,
        created_by_user_id=current_user.id,
        title=payload.title,
        department=payload.department,
        location=payload.location,
        employment_type=payload.employment_type,
        remote_option=payload.remote_option,
        salary_min=payload.salary_min,
        salary_max=payload.salary_max,
        currency=payload.currency,
        description=payload.description,
        required_skills=payload.required_skills,
        nice_to_have_skills=payload.nice_to_have_skills,
        status=payload.status or "open",
        is_public=payload.is_public or False,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("/{job_id}", response_model=JobOut)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(Job).filter(Job.id == job_id, Job.org_id == current_user.org_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.patch("/{job_id}", response_model=JobOut)
def update_job(
    job_id: int,
    payload: JobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(Job).filter(Job.id == job_id, Job.org_id == current_user.org_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(job, key, value)

    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(Job).filter(Job.id == job_id, Job.org_id == current_user.org_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    db.delete(job)
    db.commit()
    return
