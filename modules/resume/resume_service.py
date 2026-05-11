from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from modules import Resume, Experience, Education, Responsibility, Project, User
from schemas import UserCreate, UserUpdate
from modules.resume.resume_schema import Resume_Validation
from dependency import oauth2_scheme
from modules.user.user_controller import oauth2_scheme
from datetime import datetime, timezone


# create resume with experiences, responsibilities, projects, education
def create_resume(db: Session, payload: Resume_Validation, current_user: dict):
    try:
        client_id = current_user["id"]
        data = payload.model_dump(mode="json")

        # -------------------------
        # Extract child collections
        # -------------------------
        data["client_id"] = client_id
        data["is_personalinfo_fill"] = True
        data["is_summary_fill"] = True
        data["is_experience_fill"] = True
        data["is_project_fill"] = True
        data["is_education_fill"] = True
        data["is_skills_fill"] = True
        data["is_preview_fill"] = True

        experiences = data.pop("experiences")
        projects = data.pop("projects")
        education = data.pop("education")

        # -------------------------
        # Create Resume
        # -------------------------
        resume = Resume(**data)
        db.add(resume)
        db.flush()  # get resume.id

        # -------------------------
        # Experiences + Responsibilities
        # -------------------------
        experience_rows = []
        responsibility_rows = []

        for exp in experiences:
            exp_model = Experience(
                resume_id=resume.id,
                position=exp["position"],
                company=exp["company"],
                startDate=exp["startDate"],
                endDate=exp["endDate"],
                techStack=exp["techStack"],
            )
            experience_rows.append(exp_model)

        db.add_all(experience_rows)
        db.flush()  # get experience IDs

        # Map responsibilities
        for exp_model, exp in zip(experience_rows, experiences):
            responsibility_rows.extend(
                Responsibility(experience_id=exp_model.id, text=resp)
                for resp in exp["responsibilities"]
            )

        db.add_all(responsibility_rows)

        # -------------------------
        # Projects (bulk insert)
        # -------------------------
        db.add_all(
            [
                Project(
                    resume_id=resume.id,
                    name=p["name"],
                    description=p["description"],
                    techStack=p["techStack"],
                    github=p.get("github"),
                    live=p.get("live"),
                )
                for p in projects
            ]
        )

        # -------------------------
        # Education (bulk insert)
        # -------------------------
        db.add_all(
            [
                Education(
                    resume_id=resume.id,
                    degree=e["degree"],
                    institution=e["institution"],
                    startYear=e["startYear"],
                    endYear=e["endYear"],
                )
                for e in education
            ]
        )

        db.commit()
        return {"message": "Resume created successfully", "statusCode": 201}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# fetch all resumes with nested experiences, responsibilities, projects, education
def get_all_resume(db: Session, current_user: dict):
    try:
        print("current_user---->", current_user)

        # Safely get client_id
        client_id = current_user.get("id") or current_user.get("user_id")

        print("client_id---->", client_id)

        if not client_id:
            raise HTTPException(status_code=400, detail="User ID not found")

        resume = (
            db.query(Resume)
            .filter(Resume.client_id == client_id)
            .options(
                joinedload(Resume.experiences).joinedload(Experience.responsibilities),
                joinedload(Resume.projects),
                joinedload(Resume.education),
            )
            .filter(Resume.is_deleted == False)
            .all()
        )

        # If no resume found
        if not resume:
            raise HTTPException(status_code=404, detail="No resume found")

        fetch_resume_list = []

        for res in resume:
            exp_list = []

            for exp in res.experiences:
                resp_list = [resp.text for resp in exp.responsibilities]

                exp_list.append(
                    {
                        "position": exp.position,
                        "company": exp.company,
                        "startDate": exp.startDate,
                        "endDate": exp.endDate,
                        "techStack": exp.techStack,
                        "responsibilities": resp_list,
                    }
                )

            proj_list = [
                {
                    "name": proj.name,
                    "description": proj.description,
                    "techStack": proj.techStack,
                    "github": proj.github,
                    "live": proj.live,
                }
                for proj in res.projects
            ]

            edu_list = [
                {
                    "degree": edu.degree,
                    "institution": edu.institution,
                    "startYear": edu.startYear,
                    "endYear": edu.endYear,
                }
                for edu in res.education
            ]

            fetch_resume_list.append(
                {
                    "id": res.id,
                    "full_name": res.fullName,
                    "email": res.email,
                    "summary": res.summary,
                    "experiences": exp_list,
                    "projects": proj_list,
                    "education": edu_list,
                    "frontend": res.frontend,
                    "backend": res.backend,
                    "database": res.database,
                    "other": res.other,
                    "title": res.title,
                    "github": res.github,
                    "linkedin": res.linkedin,
                    "portfolio": res.portfolio,
                }
            )

        return {
            "message": "Resume fetched successfully",
            "data": fetch_resume_list,
            "statusCode": 200,
        }

    except HTTPException as http_error:
        print("HTTP Exception --->", str(http_error.detail))
        raise http_error

    except Exception as e:
        print("Resume Fetch Error --->", str(e))

        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


# fetch resume by id with nested experiences, responsibilities, projects, education
def get_resume_by_id(db: Session, id: int, current_user: dict):
    client_id = current_user["id"]
    resume = (
        db.query(Resume)
        .filter(Resume.client_id == client_id)
        .options(
            joinedload(Resume.experiences).joinedload(Experience.responsibilities),
            joinedload(Resume.projects),
            joinedload(Resume.education),
        )
        .filter(Resume.id == id, Resume.is_deleted == False)
        .all()
    )
    fetch_resume_list = []
    for res in resume:
        exp_list = []
        for exp in res.experiences:
            resp_list = [resp.text for resp in exp.responsibilities]
            exp_list.append(
                {
                    "position": exp.position,
                    "company": exp.company,
                    "startDate": exp.startDate,
                    "endDate": exp.endDate,
                    "techStack": exp.techStack,
                    "responsibilities": resp_list,
                }
            )

        proj_list = [
            {
                "name": proj.name,
                "description": proj.description,
                "techStack": proj.techStack,
                "github": proj.github,
                "live": proj.live,
            }
            for proj in res.projects
        ]

        edu_list = [
            {
                "degree": edu.degree,
                "institution": edu.institution,
                "startYear": edu.startYear,
                "endYear": edu.endYear,
            }
            for edu in res.education
        ]

        fetch_resume_list.append(
            {
                "full_name": res.fullName,
                "email": res.email,
                "summary": res.summary,
                "experiences": exp_list,
                "projects": proj_list,
                "education": edu_list,
                "frontend": res.frontend,
                "backend": res.backend,
                "database": res.database,
                "other": res.other,
                "title": res.title,
                "github": res.github,
                "linkedin": res.linkedin,
                "portfolio": res.portfolio,
                "is_personalinfo_fill": res.is_personalinfo_fill,
                "is_summary_fill": res.is_summary_fill,
                "is_experience_fill": res.is_experience_fill,
                "is_project_fill": res.is_project_fill,
                "is_education_fill": res.is_education_fill,
                "is_skills_fill": res.is_skills_fill,
                "is_preview_fill": res.is_preview_fill,
            }
        )
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    return {
        "message": "Resume fetched successfully",
        "data": fetch_resume_list,
        "statusCode": 200,
    }


# update resume along with experiences, responsibilities, projects, education
def update_resume(
    db: Session, resume_id: int, data: Resume_Validation, current_user: dict
):
    try:
        client_id = current_user["id"]
        resume = (
            db.query(Resume)
            .filter(
                Resume.id == resume_id,
                Resume.client_id == client_id,
                Resume.is_deleted == False,
            )
            .first()
        )
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")

        # Update main resume fields
        resume.fullName = data.fullName
        resume.title = data.title
        resume.email = data.email
        resume.summary = data.summary
        resume.frontend = data.frontend
        resume.backend = data.backend

        resume.github = str(data.github) if data.github else None
        resume.linkedin = str(data.linkedin) if data.linkedin else None
        resume.portfolio = str(data.portfolio) if data.portfolio else None
        resume.database = data.database
        resume.other = data.other

        db.commit()

        # Delete previous child table rows
        db.query(Experience).filter(Experience.resume_id == resume_id).delete()
        db.query(Project).filter(Project.resume_id == resume_id).delete()
        db.query(Education).filter(Education.resume_id == resume_id).delete()

        # Insert updated Experience + Responsibilities
        exp_list = []
        resp_list = []

        for exp in data.experiences:
            exp_list.append(
                {
                    "resume_id": resume_id,
                    "position": exp.position,
                    "company": exp.company,
                    "startDate": exp.startDate,
                    "endDate": exp.endDate,
                    "techStack": exp.techStack,
                }
            )
        # Bulk insert experiences

        exp_result = db.execute(
            Experience.__table__.insert().returning(Experience.id), exp_list
        )
        created_exp_ids = exp_result.fetchall()
        # Insert responsibilities for each experience
        for exp_index, exp in enumerate(data.experiences):
            exp_id = created_exp_ids[exp_index][0]
            for r in exp.responsibilities:
                resp_list.append({"experience_id": exp_id, "text": r})

        if resp_list:
            db.execute(Responsibility.__table__.insert(), resp_list)

        # Insert updated Project
        project_list = [
            {
                **pr.dict(exclude_none=True),
                "github": str(pr.github) if pr.github else None,
                "live": str(pr.live) if pr.live else None,
                "resume_id": resume_id,
            }
            for pr in data.projects
        ]
        print("project_list", project_list)
        db.execute(Project.__table__.insert(), project_list)

        # Insert updated Education
        edu_list = [{**edu.dict(), "resume_id": resume_id} for edu in data.education]
        db.execute(Education.__table__.insert(), edu_list)

        db.commit()
        db.refresh(resume)

        return {
            "message": "Resume updated successfully",
            "statusCode": 201,
        }
    except Exception as e:
        print("errors123", e)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# delete resume (soft delete)
def delete_resume(db: Session, resume_id: int, current_user: dict):
    client_id = current_user["id"]
    resume = (
        db.query(Resume)
        .filter(
            Resume.id == resume_id,
            Resume.client_id == client_id,
            Resume.is_deleted == False,
        )
        .first()
    )

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    now = datetime.now(timezone.utc)

    # Soft delete resume
    resume.is_deleted = True
    resume.deleted_at = now

    # Soft delete experiences
    experiences = (
        db.query(Experience)
        .filter(Experience.resume_id == resume_id, Experience.is_deleted == False)
        .all()
    )

    for exp in experiences:
        exp.is_deleted = True
        exp.deleted_at = now

        # Soft delete responsibilities
        db.query(Responsibility).filter(
            Responsibility.experience_id == exp.id, Responsibility.is_deleted == False
        ).update({"is_deleted": True, "deleted_at": now}, synchronize_session=False)

    # Soft delete projects
    # --------------------------------
    db.query(Project).filter(
        Project.resume_id == resume_id, Project.is_deleted == False
    ).update({"is_deleted": True, "deleted_at": now}, synchronize_session=False)

    # Soft delete education
    # --------------------------------
    db.query(Education).filter(
        Education.resume_id == resume_id, Education.is_deleted == False
    ).update({"is_deleted": True, "deleted_at": now}, synchronize_session=False)

    db.commit()
    return {"message": "Resume deleted successfully", "statusCode": 200}


def get_resume(db: Session):
    # phone number repeatition  count
    try:
        counts = (
            db.query(
                Resume.phone_number, Resume.email, func.count(Resume.id).label("total")
            )
            .group_by(Resume.phone_number, Resume.email)
            .all()
        )

        # 2️⃣ Build dictionaries in a single pass
        phone_counts = {}
        email_counts = {}
        print(counts)
        for phone, email, count in counts:
            if phone:
                phone_counts[phone] = phone_counts.get(phone, 0) + count
            if email:
                email_counts[email] = email_counts.get(email, 0) + count

        query = db.query(Resume, User).options(joinedload(Resume.user))

        resumeList = [
            {
                "first_name": resume.first_name,
                "last_name": resume.last_name,
                "user": user.name,
            }
            for resume, user in query
        ]

        return {
            "statusCode": 200,
            "data": {
                "resumeList": resumeList,
                "phone_number_count": phone_counts,
                "email_count": email_counts,
            },
        }
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
