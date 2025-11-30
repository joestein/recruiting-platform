from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ...models.user import User
from ...schemas.candidates import CandidateFromResumeResponse, CandidateOut
from ...services.agent_candidates import create_candidate_from_resume
from ..deps import get_current_user, get_db

router = APIRouter(prefix="/agent/candidates", tags=["agent-candidates"])


@router.post("/from_resume", response_model=CandidateFromResumeResponse)
async def create_candidate_from_resume_endpoint(
    resume: UploadFile = File(...),
    notes: str | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not resume.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing resume file")

    file_bytes = await resume.read()

    candidate = create_candidate_from_resume(
        db=db,
        user=current_user,
        file_bytes=file_bytes,
        filename=resume.filename,
        extra_notes=notes,
    )

    summary_parts = [f"Created candidate #{candidate.id}: {candidate.full_name}."]
    if candidate.current_title:
        summary_parts.append(f" Current title: {candidate.current_title}.")
    if candidate.current_company:
        summary_parts.append(f" Current company: {candidate.current_company}.")
    if candidate.location:
        summary_parts.append(f" Location: {candidate.location}.")
    if candidate.headline:
        summary_parts.append(f" Headline: {candidate.headline}.")

    summary = " ".join(summary_parts) or f"Created candidate #{candidate.id}."

    return CandidateFromResumeResponse(
        candidate=CandidateOut.model_validate(candidate),
        summary=summary,
    )
