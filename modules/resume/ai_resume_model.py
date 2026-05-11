from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    JSON,
    ForeignKey,
    DateTime,
    func,
)
from sqlalchemy.orm import relationship
from database import Base


class Ai_Resume(Base):
    __tablename__ = "ai_resumes"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, nullable=False, index=True)  # derived from JWT token
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # relationships
    skills = relationship(
        "Ai_Skill", back_populates="resume", cascade="all, delete-orphan"
    )
    experiences = relationship(
        "Ai_Experience", back_populates="resume", cascade="all, delete-orphan"
    )
    educations = relationship(
        "Ai_Education", back_populates="resume", cascade="all, delete-orphan"
    )
    projects = relationship(
        "Ai_Project", back_populates="resume", cascade="all, delete-orphan"
    )
    certifications = relationship(
        "Ai_Certification", back_populates="resume", cascade="all, delete-orphan"
    )
    improvement = relationship(
        "Ai_Improvement",
        back_populates="resume",
        cascade="all, delete-orphan",
        uselist=False,
    )


class Ai_Skill(Base):
    __tablename__ = "ai_skills"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(
        Integer, ForeignKey("ai_resumes.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(100), nullable=False)

    resume = relationship("Ai_Resume", back_populates="skills")


class Ai_Experience(Base):
    __tablename__ = "ai_experiences"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(
        Integer, ForeignKey("ai_resumes.id", ondelete="CASCADE"), nullable=False
    )
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    duration = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)

    resume = relationship("Ai_Resume", back_populates="experiences")


class Ai_Education(Base):
    __tablename__ = "ai_educations"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(
        Integer, ForeignKey("ai_resumes.id", ondelete="CASCADE"), nullable=False
    )
    degree = Column(String(255), nullable=False)
    institution = Column(String(255), nullable=False)
    year = Column(String(50), nullable=True)

    resume = relationship("Ai_Resume", back_populates="educations")


class Ai_Project(Base):
    __tablename__ = "ai_projects"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(
        Integer, ForeignKey("ai_resumes.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    technologies = Column(Text, nullable=True)

    resume = relationship("Ai_Resume", back_populates="projects")


class Ai_Certification(Base):
    __tablename__ = "ai_certifications"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(
        Integer, ForeignKey("ai_resumes.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(255), nullable=True)

    resume = relationship("Ai_Resume", back_populates="certifications")


class Ai_Improvement(Base):
    """Stores AI-generated improvement feedback for a resume (one-to-one with Ai_Resume)."""

    __tablename__ = "ai_improvements"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(
        Integer,
        ForeignKey("ai_resumes.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    score = Column(Float, nullable=True)
    strengths = Column(JSON, nullable=True)  # list[str]
    improvements = Column(JSON, nullable=True)  # list[str]
    rewrites = Column(
        JSON, nullable=True
    )  # dict with keys: experience, frontend, project

    resume = relationship("Ai_Resume", back_populates="improvement")
