from typing import List, Optional

from pydantic import BaseModel


class CandidatesForJobRequest(BaseModel):
    job_id: int
    limit: int = 20


class CandidateMatchOut(BaseModel):
    candidate_id: int
    full_name: str
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    location: Optional[str] = None
    score: int
    reason: Optional[str] = None
    strategy: Optional[str] = None

    class Config:
        from_attributes = True


class CandidatesForJobResponse(BaseModel):
    job_id: int
    matches: List[CandidateMatchOut]


class JobsForCandidateRequest(BaseModel):
    candidate_id: int
    limit: int = 20


class JobMatchOut(BaseModel):
    job_id: int
    title: str
    location: Optional[str] = None
    status: Optional[str] = None
    score: int
    reason: Optional[str] = None
    strategy: Optional[str] = None

    class Config:
        from_attributes = True


class JobsForCandidateResponse(BaseModel):
    candidate_id: int
    matches: List[JobMatchOut]
