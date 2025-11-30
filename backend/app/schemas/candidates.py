from typing import List, Optional

from pydantic import BaseModel, HttpUrl


class CandidateBase(BaseModel):
    full_name: str
    headline: Optional[str] = None
    location: Optional[str] = None
    experience_years: Optional[int] = None
    current_title: Optional[str] = None
    current_company: Optional[str] = None

    linkedin_url: Optional[HttpUrl] = None
    github_url: Optional[HttpUrl] = None
    website_url: Optional[HttpUrl] = None

    notes: Optional[str] = None


class CandidateCreate(CandidateBase):
    pass


class CandidateUpdate(BaseModel):
    full_name: Optional[str] = None
    headline: Optional[str] = None
    location: Optional[str] = None
    experience_years: Optional[int] = None
    current_title: Optional[str] = None
    current_company: Optional[str] = None

    linkedin_url: Optional[HttpUrl] = None
    github_url: Optional[HttpUrl] = None
    website_url: Optional[HttpUrl] = None

    notes: Optional[str] = None


class CandidateOut(CandidateBase):
    id: int
    org_id: int

    class Config:
        from_attributes = True


class CandidateList(BaseModel):
    items: List[CandidateOut]
    total: int


class CandidateFromResumeResponse(BaseModel):
    candidate: CandidateOut
    summary: str
