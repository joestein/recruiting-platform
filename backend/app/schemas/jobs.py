from typing import List, Optional

from pydantic import BaseModel


class JobBase(BaseModel):
    title: str
    department: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    remote_option: Optional[str] = None

    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    currency: Optional[str] = "USD"

    description: Optional[str] = None

    required_skills: Optional[list[str]] = None
    nice_to_have_skills: Optional[list[str]] = None

    status: Optional[str] = "open"
    is_public: Optional[bool] = False


class JobCreate(JobBase):
    title: str


class JobUpdate(BaseModel):
    title: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    remote_option: Optional[str] = None

    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    currency: Optional[str] = None

    description: Optional[str] = None

    required_skills: Optional[list[str]] = None
    nice_to_have_skills: Optional[list[str]] = None

    status: Optional[str] = None
    is_public: Optional[bool] = None


class JobOut(JobBase):
    id: int
    org_id: int
    created_by_user_id: int

    class Config:
        from_attributes = True


class JobList(BaseModel):
    items: List[JobOut]
    total: int


class JobFromPromptRequest(BaseModel):
    prompt: str


class JobFromPromptResponse(BaseModel):
    raw_prompt: str
    job: JobOut


class JobFromReqResponse(BaseModel):
    filename: str
    job: JobOut
    summary: str
