import re

from fastapi import APIRouter, Depends, File, HTTPException, status, UploadFile
from openai import OpenAI
from sqlalchemy.orm import Session, joinedload
from modules.user.user_service import get_current_user
import httpx
from flask import json
from dependency import get_db
from .ai_resume_model import (
    Ai_Achievements,
    Ai_Languages,
    Ai_Resume,
    Ai_Skill,
    Ai_Experience,
    Ai_Education,
    Ai_Project,
    Ai_Certification,
    Ai_Improvement,
)
import os
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
            joinedload(Ai_Resume.languages),
            joinedload(Ai_Resume.achievements),
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

    for lang in fd.get("languages", []):
        lang_name = lang if isinstance(lang, str) else lang.get("name", "")
        if lang_name:
            db.add(Ai_Languages(resume_id=resume.id, name=lang_name))

    for ach in fd.get("achievements", []):
        ach_name = ach if isinstance(ach, str) else ach.get("name", "")
        if ach_name:
            db.add(Ai_Achievements(resume_id=resume.id, name=ach_name))

    # 7. Improvement — from root-level fields
    db.add(
        Ai_Improvement(
            resume_id=resume.id,
            score=parsed_output.get("score"),
            career_level=parsed_output.get("career_level"),
            cover_letter_hook=parsed_output.get("cover_letter_hook"),
            strengths=parsed_output.get("strengths"),
            improvements=parsed_output.get("improvements"),
            rewrites=parsed_output.get("rewrites"),
            score_breakdown=parsed_output.get("score_breakdown"),
            critical_issues=parsed_output.get("critical_issues"),
            missing_sections=parsed_output.get("missing_sections"),
            improved_summary=parsed_output.get("improved_summary"),
            ats_keywords=parsed_output.get("ats_keywords"),
            skill_suggestions=parsed_output.get("skill_suggestions"),
            experience_tips=parsed_output.get("experience_tips"),
            target_roles=parsed_output.get("target_roles"),
            industry_fit=parsed_output.get("industry_fit"),
            action_verbs=parsed_output.get("action_verbs"),
            linkedin_tips=parsed_output.get("linkedin_tips"),
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


# ─── AI JSON Repair Helper ───────────────────────────────────────────────
def _repair_json(raw: str) -> str:
    """
    Auto-repair the most common AI JSON mistakes before parsing.
    """
    text = raw.strip()

    # 1. Strip markdown fences  ```json ... ```
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```\s*$", "", text)
    text = text.strip()

    # 2. Fix missing commas between fields:
    #    "value"          <- no comma
    #    "next_key": ...
    text = re.sub(
        r'(["\d\]\}])\s*\n(\s*")',
        lambda m: m.group(1) + ",\n" + m.group(2),
        text,
    )

    # 3. Fix trailing commas before } or ]
    text = re.sub(r",\s*([}\]])", r"\1", text)

    # 4. Replace curly/smart quotes with straight quotes
    text = (
        text.replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
    )

    return text


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

    # Pass 1: try raw output directly
    try:
        return json.loads(raw_output)
    except json.JSONDecodeError:
        pass

    # Pass 2: repair then parse
    repaired = _repair_json(raw_output)
    try:
        return json.loads(repaired)
    except json.JSONDecodeError:
        pass

    # Pass 3: extract outermost { } block and parse
    match = re.search(r"\{.*\}", repaired, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Give up with debug info
    print("RAW OUTPUT (unparseable):\n", raw_output[:3000])
    raise HTTPException(500, "AI returned malformed JSON. Check server logs.")


# ─── POST /ai_resumes/analyze-resume ─────────────────────────────────────────


@ai_resume_router.post("/analyze-resume", status_code=status.HTTP_201_CREATED)
async def analyze_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),  # ← add db here
    current_user: dict = Depends(get_current_user),
):
    client_id = current_user.get("id") or current_user.get("user_id")
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
    You are an expert ATS system, resume parser, and career coach. Analyze the resume thoroughly and return ONLY valid JSON in this EXACT format with no extra text:
 
{{
  "score": <number 0-100>,
 
  "score_breakdown": {{
    "ats_compatibility": <number 0-100>,
    "content_quality":   <number 0-100>,
    "keyword_density":   <number 0-100>,
    "formatting":        <number 0-100>,
    "impact_language":   <number 0-100>
  }},
 
  "strengths": [<5 strings — what the candidate does well>],
 
  "improvements": [<5 strings — high-priority fixes needed>],
 
  "quick_wins": [<3 strings — small changes that immediately boost ATS score>],
 
  "critical_issues": [<3 strings — deal-breaker problems recruiters will notice first>],
 
  "missing_sections": [<list of strings for important sections absent from resume, e.g. "LinkedIn URL", "GitHub link", "Certifications", "Summary", empty list if none>],
 
  "rewrites": {{
    "experience": [<2 improved bullet strings>],
    "frontend":   [<2 improved bullet strings>],
    "project":    [<2 improved bullet strings>]
  }},
 
  "improved_summary": "<a polished 2-3 sentence professional summary with strong action language, rewritten from the existing one or generated if missing>",
 
  "ats_keywords": {{
    "found":   [<keywords already present in resume>],
    "missing": [<10-15 high-value ATS keywords the candidate should add based on their role/domain>]
  }},
 
  "skill_suggestions": {{
    "add":    [<5-8 in-demand skills to add based on candidate's role and tech stack>],
    "remove": [<skills that are outdated or redundant and should be dropped, empty list if none>],
    "reorder": "<advice on how to reorder skills for maximum ATS impact>"
  }},
 
  "experience_tips": [<3-4 strings — specific advice on improving each experience bullet, quantifying impact, adding metrics>],
 
  "career_level": "<one of: Junior | Mid-level | Senior | Lead | Executive — inferred from experience>",
 
  "target_roles": [<3-5 job titles this candidate is best suited for based on their skills and experience>],
 
  "industry_fit": [<2-3 industries where this profile is most competitive>],
 
  "action_verbs": {{
    "current":  [<action verbs already used in the resume>],
    "suggested": [<8-10 stronger action verbs suited to this candidate's role that they should use>]
  }},
 
  "linkedin_tips": [<2-3 strings — suggestions for optimizing LinkedIn profile based on resume content>],
 
  "cover_letter_hook": "<a compelling 1-2 sentence opening for a cover letter tailored to this candidate's strongest selling points>",
 
  "form_data": {{
    "name":     "<full name>",
    "email":    "<email address>",
    "phone":    "<phone number>",
    "location": "<city, country>",
    "linkedin": "<LinkedIn URL if present, else empty string>",
    "github":   "<GitHub URL if present, else empty string>",
    "portfolio":"<portfolio/website URL if present, else empty string>",
    "summary":  "<professional summary 2-3 sentences>",
    "skills":   [<list of skill strings>],
    "experience": [
      {{
        "title":       "<job title>",
        "company":     "<company name>",
        "duration":    "<e.g. Jan 2021 - Present>",
        "description": "<key responsibilities and achievements>"
      }}
    ],
    "education": [
      {{
        "degree":      "<degree name>",
        "institution": "<university/college name>",
        "year":        "<graduation year>"
      }}
    ],
    "projects": [
      {{
        "name":         "<project name>",
        "description":  "<what it does>",
        "technologies": "<tech stack used>",
        "link":         "<live link or GitHub URL if present, else empty string>"
      }}
    ],
    "certifications": [<list of certification strings, empty list if none>],
    "languages":      [<spoken/written languages if mentioned, empty list if none>],
    "achievements":   [<notable awards, publications, or achievements if mentioned, empty list if none>]
  }}
}}
 
Rules:
- Extract ALL data from the resume accurately; never hallucinate facts
- If a field is missing from the resume, use empty string "" or empty list []
- score_breakdown scores must average close to the top-level score
- missing_sections must only list sections truly absent from the resume
- ats_keywords.found must only contain keywords actually present in the resume text
- Do NOT return any text outside the JSON object
- Return clean, valid JSON only — no markdown, no code fences, no explanations
 
Resume:
{resume_text}
"""

    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
    }

    #     # 🔥 Use helper
    parsed_output = await call_groq_api(payload)
    print("Parsed output from AI:", parsed_output)

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
    current_user_id = current_user.get("id") or current_user.get("user_id")
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
                joinedload(Ai_Resume.languages),
                joinedload(Ai_Resume.achievements),
            )
            .filter(Ai_Resume.client_id == current_user_id)
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


@ai_resume_router.get("/{resume_id}")
def get_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    current_user_id = current_user.get("id") or current_user.get("user_id")
    resume = _load_resume(resume_id, db)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if resume.client_id != current_user_id:
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

        if payload.languages is not None:
            db.query(Ai_Languages).filter(Ai_Languages.resume_id == resume_id).delete()
            for l in payload.languages:
                if l:
                    db.add(Ai_Languages(resume_id=resume_id, name=l))

        if payload.achievements is not None:
            db.query(Ai_Achievements).filter(
                Ai_Achievements.resume_id == resume_id
            ).delete()
            for a in payload.achievements:
                if a:
                    db.add(Ai_Achievements(resume_id=resume_id, name=a))

        db.commit()

        return {"id": resume.id, "message": "Resume updated successfully"}

    except HTTPException:
        # re-raise known errors
        raise

    except Exception as e:
        print("Resume Update Error:", e)
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
