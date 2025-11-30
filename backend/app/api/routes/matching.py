from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...models.match_log import MatchLog
from ...models.user import User
from ...schemas.matching import (
    CandidateMatchOut,
    CandidatesForJobRequest,
    CandidatesForJobResponse,
    JobMatchOut,
    JobsForCandidateRequest,
    JobsForCandidateResponse,
)
from ...services.matching import rank_candidates_for_job, rank_jobs_for_candidate
from ..deps import get_current_user, get_db

router = APIRouter(prefix="/matching", tags=["matching"])


@router.post("/candidates_for_job", response_model=CandidatesForJobResponse)
def candidates_for_job(
    payload: CandidatesForJobRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        matches = rank_candidates_for_job(
            db=db,
            org_id=current_user.org_id,
            job_id=payload.job_id,
            limit=payload.limit,
        )
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    out_matches: list[CandidateMatchOut] = []

    for m in matches:
        c = m.candidate
        log = MatchLog(
            org_id=current_user.org_id,
            job_id=payload.job_id,
            candidate_id=c.id,
            score=m.score,
            strategy=m.strategy,
            reason=m.reason,
        )
        db.add(log)

        out_matches.append(
            CandidateMatchOut(
                candidate_id=c.id,
                full_name=c.full_name,
                current_title=c.current_title,
                current_company=c.current_company,
                location=c.location,
                score=m.score,
                reason=m.reason,
                strategy=m.strategy,
            )
        )

    db.commit()
    return CandidatesForJobResponse(job_id=payload.job_id, matches=out_matches)


@router.post("/jobs_for_candidate", response_model=JobsForCandidateResponse)
def jobs_for_candidate(
    payload: JobsForCandidateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        matches = rank_jobs_for_candidate(
            db=db,
            org_id=current_user.org_id,
            candidate_id=payload.candidate_id,
            limit=payload.limit,
        )
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

    out_matches: list[JobMatchOut] = []

    for m in matches:
        j = m.job
        log = MatchLog(
            org_id=current_user.org_id,
            job_id=j.id,
            candidate_id=payload.candidate_id,
            score=m.score,
            strategy=m.strategy,
            reason=m.reason,
        )
        db.add(log)

        out_matches.append(
            JobMatchOut(
                job_id=j.id,
                title=j.title,
                location=j.location,
                status=j.status,
                score=m.score,
                reason=m.reason,
                strategy=m.strategy,
            )
        )

    db.commit()
    return JobsForCandidateResponse(candidate_id=payload.candidate_id, matches=out_matches)
