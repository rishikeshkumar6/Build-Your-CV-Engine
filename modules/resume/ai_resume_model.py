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
    languages = relationship(
        "Ai_Languages", back_populates="resume", cascade="all, delete-orphan"
    )
    achievements = relationship(
        "Ai_Achievements", back_populates="resume", cascade="all, delete-orphan"
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


class Ai_Languages(Base):
    __tablename__ = "ai_languages"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(
        Integer, ForeignKey("ai_resumes.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(255), nullable=True)

    resume = relationship("Ai_Resume", back_populates="languages")


class Ai_Achievements(Base):
    __tablename__ = "ai_achievements"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(
        Integer, ForeignKey("ai_resumes.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(255), nullable=True)

    resume = relationship("Ai_Resume", back_populates="achievements")


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
    career_level = Column(Text, nullable=True)  # ✅ fixed
    cover_letter_hook = Column(Text, nullable=True)  # ✅ fixed
    strengths = Column(JSON, nullable=True)
    improvements = Column(JSON, nullable=True)
    rewrites = Column(JSON, nullable=True)
    score_breakdown = Column(JSON, nullable=True)  # ✅ fixed
    critical_issues = Column(JSON, nullable=True)  # ✅ fixed
    missing_sections = Column(JSON, nullable=True)  # ✅ fixed
    improved_summary = Column(Text, nullable=True)  # ✅ fixed
    ats_keywords = Column(JSON, nullable=True)  # ✅ fixed
    skill_suggestions = Column(JSON, nullable=True)  # ✅ fixed
    experience_tips = Column(JSON, nullable=True)  # ✅ fixed
    target_roles = Column(JSON, nullable=True)  # ✅ fixed
    industry_fit = Column(JSON, nullable=True)  # ✅ fixed
    action_verbs = Column(JSON, nullable=True)  # ✅ fixed
    linkedin_tips = Column(JSON, nullable=True)  # ✅ fixed

    resume = relationship("Ai_Resume", back_populates="improvement")
