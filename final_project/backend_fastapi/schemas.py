from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class CompanyBase(BaseModel):
    name: str
    description: Optional[str] = None
    website: Optional[str] = None


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None


class CompanyResponse(CompanyBase):
    id: int

    class Config:
        from_attributes = True


class JobBase(BaseModel):
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    salary: Optional[str] = None
    company_id: Optional[int] = None
    is_active: bool = True


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    salary: Optional[str] = None
    company_id: Optional[int] = None
    is_active: Optional[bool] = None


class JobResponse(JobBase):
    id: int
    posted_date: datetime
    posted_by: Optional[str] = None
    company: Optional[CompanyResponse] = None

    class Config:
        from_attributes = True


class ApplicationCreate(BaseModel):
    job_id: int
    applicant_name: str
    experience: str
    skills: str
    cover_letter: Optional[str] = None
    resume_url: Optional[str] = None


class ApplicationResponse(BaseModel):
    id: int
    job_id: int
    candidate_id: int
    status: str
    applied_at: datetime
    applicant_name: Optional[str] = None
    experience: Optional[str] = None
    skills: Optional[str] = None
    cover_letter: Optional[str] = None
    resume_url: Optional[str] = None
    job: Optional[JobResponse] = None

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class TokenData(BaseModel):
    username: Optional[str] = None
