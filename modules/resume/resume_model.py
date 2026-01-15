from sqlalchemy import Column, Integer, String, ForeignKey, JSON, Date, Text, Boolean
from sqlalchemy.orm import relationship
from database import Base
from typing import List
from sqlalchemy.types import DateTime


# ------------------------------------
# Resume MAIN MODEL
# ------------------------------------
class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    fullName = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)

    github = Column(String(500), nullable=True)
    linkedin = Column(String(500), nullable=True)
    portfolio = Column(String(500), nullable=True)

    summary = Column(Text, nullable=False)

    frontend = Column(Text, nullable=False)
    backend = Column(Text, nullable=False)
    database = Column(Text, nullable=False)
    other = Column(Text, nullable=False)
    is_personalinfo_fill = Column(Boolean, default=False, nullable=False)
    is_summary_fill = Column(Boolean, default=False, nullable=False)
    is_experience_fill = Column(Boolean, default=False, nullable=False)
    is_project_fill = Column(Boolean, default=False, nullable=False)
    is_education_fill = Column(Boolean, default=False, nullable=False)
    is_skills_fill = Column(Boolean, default=False, nullable=False)
    is_preview_fill = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    experiences = relationship(
        "Experience", back_populates="resume", cascade="all, delete-orphan"
    )
    projects = relationship(
        "Project", back_populates="resume", cascade="all, delete-orphan"
    )
    education = relationship(
        "Education", back_populates="resume", cascade="all, delete-orphan"
    )
    users = relationship("User", back_populates="resumes")


# ------------------------------------
# EXPERIENCE MODEL
# ------------------------------------
class Experience(Base):
    __tablename__ = "experiences"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"))

    position = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    startDate = Column(Date, nullable=False)
    endDate = Column(Date, nullable=False)

    techStack = Column(Text, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    resume = relationship("Resume", back_populates="experiences")

    # CHILD TABLE FOR RESPONSIBILITIES
    responsibilities = relationship(
        "Responsibility",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


# ------------------------------------
# RESPONSIBILITY MODEL
# ------------------------------------
class Responsibility(Base):
    __tablename__ = "responsibilities"

    id = Column(Integer, primary_key=True, index=True)
    experience_id = Column(Integer, ForeignKey("experiences.id", ondelete="CASCADE"))

    text = Column(String(255), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    experience = relationship("Experience", back_populates="responsibilities")


# ------------------------------------
# PROJECT MODEL
# ------------------------------------
class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"))

    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    techStack = Column(String(200), nullable=False)
    github = Column(String(500), nullable=True)
    live = Column(String(500), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    resume = relationship("Resume", back_populates="projects")


# ------------------------------------
# EDUCATION MODEL
# ------------------------------------
class Education(Base):
    __tablename__ = "education"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"))

    degree = Column(String(255), nullable=False)
    institution = Column(String(255), nullable=False)
    startYear = Column(Date, nullable=False)
    endYear = Column(Date, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    resume = relationship("Resume", back_populates="education")
