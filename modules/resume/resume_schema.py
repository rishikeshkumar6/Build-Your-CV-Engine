from pydantic import (
    BaseModel,
    EmailStr,
    HttpUrl,
    StringConstraints,
    validator,
    Field,
    constr,
    field_validator,
    model_validator,
)
import re
from typing import Optional, List, Any
from datetime import date
from typing_extensions import Annotated


# -----------------------------
# Experience Schema
# -----------------------------
class Experience(BaseModel):
    position: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    company: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    startDate: date
    endDate: date

    responsibilities: List[str] = Field(
        ..., min_items=1, description="At least one responsibility"
    )

    techStack: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


# -----------------------------
# Project Schema
# -----------------------------
class Project(BaseModel):
    name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
    ]
    description: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)
    ]
    techStack: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
    ]
    github: Optional[HttpUrl] = None
    live: Optional[HttpUrl] = None


# -----------------------------
# Education Schema
# -----------------------------
class Education(BaseModel):
    degree: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    institution: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    startYear: date
    endYear: date


# -----------------------------
# MAIN RESUME SCHEMA
# -----------------------------
class Resume_Validation(BaseModel):
    # personalInfoSchema
    fullName: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=2,
            max_length=100,
            pattern=r"^[A-Za-z\s]+$",
        ),
    ]

    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

    email: EmailStr

    github: Optional[HttpUrl] = None
    linkedin: Optional[HttpUrl] = None
    portfolio: Optional[HttpUrl] = None

    # summarySchema
    summary: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=10, max_length=500)
    ]

    # exprienceSchema
    experiences: List[Experience] = Field(..., min_items=1)

    # projectsSchema
    projects: List[Project] = Field(..., min_items=1)

    # educationSchema
    education: List[Education] = Field(..., min_items=1)

    # skillsSchema
    frontend: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    backend: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    database: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    other: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class GetResumeResponse(BaseModel):
    message: str
    statusCode: int
    data: Optional[Any] = None

    class Config:
        orm_mode = True
