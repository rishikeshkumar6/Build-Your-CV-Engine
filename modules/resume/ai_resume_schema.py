from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, EmailStr, model_validator

# ─── Skill ───────────────────────────────────────────────────────────────────


class SkillCreate(BaseModel):
    name: str

    @model_validator(mode="before")
    @classmethod
    def coerce_string(cls, value):
        if isinstance(value, str):
            return {"name": value}
        return value


class SkillOut(SkillCreate):
    id: int

    class Config:
        from_attributes = True


# ─── Experience ───────────────────────────────────────────────────────────────


class ExperienceCreate(BaseModel):
    title: str
    company: str
    duration: Optional[str] = None
    description: Optional[str] = None


class ExperienceOut(ExperienceCreate):
    id: int

    class Config:
        from_attributes = True


# ─── Education ────────────────────────────────────────────────────────────────


class EducationCreate(BaseModel):
    degree: str
    institution: str
    year: Optional[str] = None


class EducationOut(EducationCreate):
    id: int

    class Config:
        from_attributes = True


# ─── Project ──────────────────────────────────────────────────────────────────


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    technologies: Optional[str] = None


class ProjectOut(ProjectCreate):
    id: int

    class Config:
        from_attributes = True


# ─── Certification ────────────────────────────────────────────────────────────


class CertificationCreate(BaseModel):
    name: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def coerce_string(cls, value):
        if isinstance(value, str):
            return {"name": value if value else None}
        return value


class CertificationOut(CertificationCreate):
    id: int

    class Config:
        from_attributes = True


# ─── Improvement ──────────────────────────────────────────────────────────────


class ImprovementCreate(BaseModel):
    score: Optional[float] = None
    strengths: Optional[list[str]] = None
    improvements: Optional[list[str]] = None
    rewrites: Optional[dict] = None


class ImprovementOut(ImprovementCreate):
    id: int

    class Config:
        from_attributes = True


# ─── FormData ─────────────────────────────────────────────────────────────────
# Matches the nested "form_data" block sent by the frontend.
# NOTE: frontend uses singular keys "experience" and "education" (not plural).


class FormData(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    skills: list[SkillCreate] = []
    experience: list[ExperienceCreate] = []
    education: list[EducationCreate] = []
    projects: list[ProjectCreate] = []
    certifications: list[CertificationCreate] = []


# ─── ResumeCreate ─────────────────────────────────────────────────────────────


class ResumeCreate(BaseModel):
    """
    Matches the actual frontend payload shape:
    {
        "score": 90,
        "strengths": [...],
        "improvements": [...],
        "rewrites": {"experience": [...], "frontend": [...], "project": [...]},
        "form_data": { "name": ..., "email": ..., "skills": [...], ... }
    }
    """

    client_id: int
    score: Optional[float] = None
    strengths: Optional[list[str]] = None
    improvements: Optional[list[str]] = None
    rewrites: Optional[dict] = None
    form_data: FormData


# ─── ResumeUpdate ─────────────────────────────────────────────────────────────
# Flat structure (no form_data wrapper). improvement is excluded — never updated.
# All child lists use singular keys matching the frontend payload.


class ResumeUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    skills: Optional[list[SkillCreate]] = None
    experience: Optional[list[ExperienceCreate]] = None  # singular key
    education: Optional[list[EducationCreate]] = None  # singular key
    projects: Optional[list[ProjectCreate]] = None
    certifications: Optional[list[CertificationCreate]] = None
    languages: Optional[list[str]] = None
    achievements: Optional[list[str]] = None


# ─── ResumeOut ────────────────────────────────────────────────────────────────


class ResumeOut(BaseModel):
    id: int
    client_id: int
    name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    skills: list[SkillOut] = []
    experiences: list[ExperienceOut] = []
    educations: list[EducationOut] = []
    projects: list[ProjectOut] = []
    certifications: list[CertificationOut] = []
    languages: list[str] = []
    achievements: list[str] = []
    improvement: Optional[ImprovementOut] = None

    class Config:
        from_attributes = True
