from fastapi import APIRouter, Depends, File, HTTPException, status, UploadFile
from openai import OpenAI
from sqlalchemy.orm import Session, joinedload
from modules.user.user_service import get_current_user
import httpx
import pdfplumber
from flask import json
from dependency import get_db
from .ai_resume_model import (
    Ai_Resume,
    Ai_Skill,
    Ai_Experience,
    Ai_Education,
    Ai_Project,
    Ai_Certification,
    Ai_Improvement,
)
import os
import io
from .ai_resume_schema import ResumeCreate, ResumeOut, ResumeUpdate

ai_resume_router = APIRouter(prefix="/ai_resumes", tags=["Resumes"])

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OCR_API_KEY = os.getenv("OCR_API_KEY")
OCR_API_URL = os.getenv("OCR_API_URL")
GROQ_MODEL = os.getenv("GROQ_MODEL")
GROQ_API_URL = os.getenv("GROQ_API_URL")


# ─── Helper: load resume with joinedload ──────────────────────────────────────


def _load_resume(resume_id: int, db: Session) -> Ai_Resume:
    return (
        db.query(Ai_Resume)
        .options(
            joinedload(Ai_Resume.skills),
            joinedload(Ai_Resume.experiences),
            joinedload(Ai_Resume.educations),
            joinedload(Ai_Resume.projects),
            joinedload(Ai_Resume.certifications),
            joinedload(Ai_Resume.improvement),
        )
        .filter(Ai_Resume.id == resume_id)
        .first()
    )


# ─── Helper: save resume to DB (shared by both endpoints) ────────────────────


def _save_resume_to_db(parsed_output: dict, client_id: int, db: Session) -> Ai_Resume:
    """
    Takes the raw parsed_output dict (from AI or hardcoded) + client_id,
    saves everything to DB, and returns the fully loaded resume ORM object.
    """
    fd = parsed_output.get("form_data", {})

    # 1. Core resume row
    resume = Ai_Resume(
        client_id=client_id,
        name=fd.get("name", ""),
        email=fd.get("email", ""),
        phone=fd.get("phone", ""),
        location=fd.get("location", ""),
        summary=fd.get("summary", ""),
    )
    db.add(resume)
    db.flush()  # populate resume.id

    # 2. Skills — accepts both plain strings and dicts
    for s in fd.get("skills", []):
        name = s if isinstance(s, str) else s.get("name", "")
        if name:
            db.add(Ai_Skill(resume_id=resume.id, name=name))

    # 3. Experiences
    for e in fd.get("experience", []):
        db.add(
            Ai_Experience(
                resume_id=resume.id,
                title=e.get("title", ""),
                company=e.get("company", ""),
                duration=e.get("duration", ""),
                description=e.get("description", ""),
            )
        )

    # 4. Educations
    for edu in fd.get("education", []):
        db.add(
            Ai_Education(
                resume_id=resume.id,
                degree=edu.get("degree", ""),
                institution=edu.get("institution", ""),
                year=edu.get("year", ""),
            )
        )

    # 5. Projects
    for p in fd.get("projects", []):
        db.add(
            Ai_Project(
                resume_id=resume.id,
                name=p.get("name", ""),
                description=p.get("description", ""),
                technologies=p.get("technologies", ""),
            )
        )

    # 6. Certifications — skip empty strings
    for c in fd.get("certifications", []):
        cert_name = c if isinstance(c, str) else c.get("name", "")
        if cert_name:
            db.add(Ai_Certification(resume_id=resume.id, name=cert_name))

    # 7. Improvement — from root-level fields
    db.add(
        Ai_Improvement(
            resume_id=resume.id,
            score=parsed_output.get("score"),
            strengths=parsed_output.get("strengths"),
            improvements=parsed_output.get("improvements"),
            rewrites=parsed_output.get("rewrites"),
        )
    )

    db.commit()
    return _load_resume(resume.id, db)


# ─── POST /ai_resumes (direct create) ────────────────────────────────────────


@ai_resume_router.post("/", status_code=status.HTTP_201_CREATED)
def create_resume(
    payload: ResumeCreate,
    db: Session = Depends(get_db),
):
    print("Payload received for resume creation:", payload)

    resume = _save_resume_to_db(
        parsed_output=payload.model_dump(),
        client_id=payload.client_id,
        db=db,
    )
    return {"id": resume.id, "message": "Resume created successfully"}


# ─── OCR API helper ─────────────────────────────────────────────────────────
async def ocr_with_api(file_bytes):
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            OCR_API_URL,
            files={"file": ("resume.pdf", file_bytes)},
            data={"apikey": OCR_API_KEY, "language": "eng"},
        )

    result = response.json()

    if result.get("IsErroredOnProcessing"):
        return ""

    try:
        return result["ParsedResults"][0]["ParsedText"]
    except Exception:
        return ""


# ─── Groq API helper (unchanged) ──────────────────────────────────────────────


async def call_groq_api(payload: dict) -> dict:
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            GROQ_API_URL,
            json=payload,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
        )

    if resp.status_code != 200:
        raise HTTPException(500, f"Groq API Error: {resp.text}")

    result = resp.json()

    try:
        raw_output = result["choices"][0]["message"]["content"]
    except Exception:
        raise HTTPException(500, "Invalid response structure from AI")

    # Strip markdown code fences if present
    clean = raw_output.strip()
    if clean.startswith("```"):
        clean = clean.split("```", 2)[-1] if clean.count("```") >= 2 else clean
        clean = clean.lstrip("json").strip().rstrip("```").strip()

    try:
        return json.loads(clean)
    except Exception:
        print("RAW OUTPUT:", raw_output)
        raise HTTPException(500, "Invalid JSON from AI")


# ─── POST /ai_resumes/analyze-resume ─────────────────────────────────────────


@ai_resume_router.post("/analyze-resume", status_code=status.HTTP_201_CREATED)
async def analyze_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),  # ← add db here
    current_user: dict = Depends(get_current_user),
):
    client_id = current_user["id"]
    print("Client ID for resume analysis:", client_id)

    content = await file.read()

    # 🔹 Step 2: If no text → use OCR API (no Tesseract)
    resume_text = await ocr_with_api(content)
    print(
        "Final extracted text length after OCR:", len(resume_text), resume_text[:3000]
    )  # debug
    # 🔹 Step 3: If still no text → error
    if not resume_text.strip():
        raise HTTPException(
            400,
            "Could not extract text even with OCR API. Upload a clearer resume.",
        )

    # 🔹 Limit text
    resume_text = resume_text[:35000]

    # 🔹 AI Prompt
    prompt = f"""
    You are an expert ATS system and resume parser. Analyze the resume and return ONLY valid JSON in this EXACT format with no extra text:

    {{
      "score": <number 0-100>,
      "strengths": [<5 strings>],
      "improvements": [<5 strings>],
      "rewrites": {{
        "experience": [<2 improved bullet strings>],
        "frontend": [<2 improved bullet strings>],
        "project": [<2 improved bullet strings>]
      }},
      "form_data": {{
        "name": "<full name>",
        "email": "<email address>",
        "phone": "<phone number>",
        "location": "<city, country>",
        "summary": "<professional summary 2-3 sentences>",
        "skills": [<list of skill strings>],
        "experience": [
          {{
            "title": "<job title>",
            "company": "<company name>",
            "duration": "<e.g. Jan 2021 - Present>",
            "description": "<key responsibilities and achievements>"
          }}
        ],
        "education": [
          {{
            "degree": "<degree name>",
            "institution": "<university/college name>",
            "year": "<graduation year>"
          }}
        ],
        "projects": [
          {{
            "name": "<project name>",
            "description": "<what it does>",
            "technologies": "<tech stack used>"
          }}
        ],
        "certifications": [<list of certification strings, empty list if none>]
      }}
    }}

    Rules:
    - Extract ALL data from the resume accurately
    - If a field is missing from resume, use empty string "" or empty list []
    - Do NOT return any text outside the JSON object
    - Return clean, valid JSON only

    Resume:
    {resume_text}
    """

    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
    }

    #     # 🔥 Use helper
    parsed_output = await call_groq_api(payload)

    # ── Directly call DB save — no HTTP self-call needed ─────────────────────
    try:
        resume = _save_resume_to_db(parsed_output, client_id, db)
    except Exception as e:
        print("Error saving resume to DB:", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create resume: {str(e)}",
        )

    return {
        "id": resume.id,
        "message": "Resume analyzed and saved successfully",
    }


# ─── GET /ai_resumes ─────────────────────────────────────────────────────────


from fastapi import HTTPException
from sqlalchemy.orm import joinedload


@ai_resume_router.get("/")
def get_my_resumes(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        resumes = (
            db.query(Ai_Resume)
            .options(
                joinedload(Ai_Resume.skills),
                joinedload(Ai_Resume.experiences),
                joinedload(Ai_Resume.educations),
                joinedload(Ai_Resume.projects),
                joinedload(Ai_Resume.certifications),
                joinedload(Ai_Resume.improvement),
            )
            .filter(Ai_Resume.client_id == current_user["user_id"])
            .all()
        )

        if not resumes:
            return {
                "statusCode": 404,
                "message": "No resume found",
                "data": [],
            }

        return {
            "statusCode": 200,
            "message": "Resume fetched successfully",
            "data": resumes,
        }

    except Exception as e:
        print("Resume Fetch Error:", e)

        raise HTTPException(
            status_code=500,
            detail="Something went wrong while fetching resumes",
        )


# ─── GET /ai_resumes/{resume_id} ─────────────────────────────────────────────


@ai_resume_router.get("/{resume_id}", response_model=ResumeOut)
def get_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    resume = _load_resume(resume_id, db)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if resume.client_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return resume


@ai_resume_router.put("/{resume_id}", status_code=status.HTTP_200_OK)
def update_resume(
    resume_id: int,
    payload: ResumeUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        # 1. Load resume
        resume = db.query(Ai_Resume).filter(Ai_Resume.id == resume_id).first()
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")

        if resume.client_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # 2. Update scalar fields
        if payload.name is not None:
            resume.name = payload.name
        if payload.email is not None:
            resume.email = payload.email
        if payload.phone is not None:
            resume.phone = payload.phone
        if payload.location is not None:
            resume.location = payload.location
        if payload.summary is not None:
            resume.summary = payload.summary

        # 3. Skills
        if payload.skills is not None:
            db.query(Ai_Skill).filter(Ai_Skill.resume_id == resume_id).delete()
            for s in payload.skills:
                if s.name:
                    db.add(Ai_Skill(resume_id=resume_id, name=s.name))

        # 4. Experience
        if payload.experience is not None:
            db.query(Ai_Experience).filter(
                Ai_Experience.resume_id == resume_id
            ).delete()
            for e in payload.experience:
                db.add(
                    Ai_Experience(
                        resume_id=resume_id,
                        title=e.title,
                        company=e.company,
                        duration=e.duration,
                        description=e.description,
                    )
                )

        # 5. Education
        if payload.education is not None:
            db.query(Ai_Education).filter(Ai_Education.resume_id == resume_id).delete()
            for edu in payload.education:
                db.add(
                    Ai_Education(
                        resume_id=resume_id,
                        degree=edu.degree,
                        institution=edu.institution,
                        year=edu.year,
                    )
                )

        # 6. Projects
        if payload.projects is not None:
            db.query(Ai_Project).filter(Ai_Project.resume_id == resume_id).delete()
            for p in payload.projects:
                db.add(
                    Ai_Project(
                        resume_id=resume_id,
                        name=p.name,
                        description=p.description,
                        technologies=p.technologies,
                    )
                )

        # 7. Certifications
        if payload.certifications is not None:
            db.query(Ai_Certification).filter(
                Ai_Certification.resume_id == resume_id
            ).delete()
            for c in payload.certifications:
                if c.name:
                    db.add(Ai_Certification(resume_id=resume_id, name=c.name))

        db.commit()

        return {"id": resume.id, "message": "Resume updated successfully"}

    except HTTPException:
        # re-raise known errors
        raise

    except Exception as e:
        db.rollback()  # 🔥 VERY IMPORTANT
        # logger.error(f"Error updating resume: {str(e)}")

        raise HTTPException(
            status_code=500, detail="Something went wrong while updating resume"
        )


# ─── DELETE /ai_resumes/{resume_id} ──────────────────────────────────────────


@ai_resume_router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        # 1. Fetch resume
        resume = db.query(Ai_Resume).filter(Ai_Resume.id == resume_id).first()

        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")

        # 2. Ownership check
        if resume.client_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # 3. Delete
        db.delete(resume)
        db.commit()

        return None  # 204 No Content

    except HTTPException:
        # Let FastAPI handle known errors
        raise

    except Exception as e:
        db.rollback()  # 🔥 critical

        raise HTTPException(
            status_code=500, detail="Something went wrong while deleting resume"
        )
