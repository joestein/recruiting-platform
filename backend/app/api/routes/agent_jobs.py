from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from ...models.user import User
from ...schemas.jobs import JobFromPromptRequest, JobFromPromptResponse, JobFromReqResponse, JobOut
from ...services.agent_jobs import create_job_from_prompt, create_job_from_req
from ..deps import get_current_user, get_db

router = APIRouter(prefix="/agent/jobs", tags=["agent-jobs"])


@router.post("/from_prompt", response_model=JobFromPromptResponse)
def create_job_from_prompt_endpoint(
    payload: JobFromPromptRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = create_job_from_prompt(db=db, user=current_user, prompt=payload.prompt)
    job_out = JobOut.model_validate(job)
    return JobFromPromptResponse(raw_prompt=payload.prompt, job=job_out)


@router.post("/from_req", response_model=JobFromReqResponse)
async def create_job_from_req_endpoint(
    job_req: UploadFile = File(...),
    notes: str | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_bytes = await job_req.read()

    job = create_job_from_req(
        db=db,
        user=current_user,
        file_bytes=file_bytes,
        filename=job_req.filename,
        extra_notes=notes,
    )

    skills = job.required_skills or []
    skills_str = ", ".join(skills) if skills else "N/A"

    summary = (
        f"I've created a new job from the uploaded file '{job_req.filename}':\n\n"
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
        f"- 'list jobs' to see it among your openings."
    )

    return JobFromReqResponse(
        filename=job_req.filename,
        job=JobOut.model_validate(job),
        summary=summary,
    )
