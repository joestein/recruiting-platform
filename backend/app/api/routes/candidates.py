from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ...models.candidate import Candidate
from ...models.user import User
from ...schemas.candidates import CandidateCreate, CandidateList, CandidateOut, CandidateUpdate
from ..deps import get_current_user, get_db

router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.get("", response_model=CandidateList)
def list_candidates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = Query(50, le=100),
    q: Optional[str] = None,
):
    query = db.query(Candidate).filter(Candidate.org_id == current_user.org_id)
    if q:
        like = f"%{q}%"
        query = query.filter(Candidate.full_name.ilike(like))

    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return CandidateList(items=items, total=total)


@router.post("", response_model=CandidateOut, status_code=status.HTTP_201_CREATED)
def create_candidate(
    payload: CandidateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    candidate = Candidate(
        org_id=current_user.org_id,
        full_name=payload.full_name,
        headline=payload.headline,
        location=payload.location,
        experience_years=payload.experience_years,
        current_title=payload.current_title,
        current_company=payload.current_company,
        linkedin_url=str(payload.linkedin_url) if payload.linkedin_url else None,
        github_url=str(payload.github_url) if payload.github_url else None,
        website_url=str(payload.website_url) if payload.website_url else None,
        notes=payload.notes,
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate


@router.get("/{candidate_id}", response_model=CandidateOut)
def get_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    candidate = (
        db.query(Candidate)
        .filter(Candidate.id == candidate_id, Candidate.org_id == current_user.org_id)
        .first()
    )
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


@router.patch("/{candidate_id}", response_model=CandidateOut)
def update_candidate(
    candidate_id: int,
    payload: CandidateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    candidate = (
        db.query(Candidate)
        .filter(Candidate.id == candidate_id, Candidate.org_id == current_user.org_id)
        .first()
    )
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(candidate, key, value)

    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate


@router.delete("/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    candidate = (
        db.query(Candidate)
        .filter(Candidate.id == candidate_id, Candidate.org_id == current_user.org_id)
        .first()
    )
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    db.delete(candidate)
    db.commit()
    return
