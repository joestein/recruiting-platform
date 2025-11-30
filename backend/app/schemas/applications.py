from typing import List, Optional

from pydantic import BaseModel


class ApplicationBase(BaseModel):
    status: Optional[str] = "sourced"
    source: Optional[str] = "manual"
    fit_score: Optional[int] = None


class ApplicationCreate(ApplicationBase):
    job_id: int
    candidate_id: int


class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    source: Optional[str] = None
    fit_score: Optional[int] = None


class ApplicationOut(ApplicationBase):
    id: int
    org_id: int
    job_id: int
    candidate_id: int

    class Config:
        from_attributes = True


class ApplicationList(BaseModel):
    items: List[ApplicationOut]
    total: int
