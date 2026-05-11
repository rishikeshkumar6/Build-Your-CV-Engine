from concurrent.futures import ThreadPoolExecutor
import sys
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .resume_schema import Ai_ResumeData as ResumeData
from .resume_templates import TEMPLATE_BUILDERS, build_classic_pdf
import io
from dependency import get_db
from pypdf import PdfWriter
from .resume_service import (
    create_resume,
    get_resume,
    get_resume_by_id,
    get_all_resume,
    update_resume,
    delete_resume,
)
from .resume_schema import Resume_Validation, GetResumeResponse
from modules.user.user_service import get_current_user

resumeRouter = APIRouter(tags=["resume"], prefix="/resume")


# create resume route
@resumeRouter.post("/create", response_model=GetResumeResponse)
def create(
    resume: Resume_Validation,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return create_resume(db, resume, current_user)


# ── Endpoint ───────────────────────────────────────────────────────────────────


@resumeRouter.post("/api/download-resume")
async def download_resume(data: ResumeData):
    builder = TEMPLATE_BUILDERS.get(data.template, build_classic_pdf)

    try:
        # Build PDF with ReportLab
        pdf_bytes = builder(data)

        # Pass through PdfWriter to normalize, compress, and finalize the PDF
        reader_buf = io.BytesIO(pdf_bytes)
        from pypdf import PdfReader

        reader = PdfReader(reader_buf)
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        # Optional metadata
        writer.add_metadata(
            {
                "/Author": data.name,
                "/Title": f"{data.name} - Resume",
                "/Subject": "Resume",
                "/Creator": "Resume Builder",
            }
        )

        # Write final PDF
        output_buf = io.BytesIO()
        writer.write(output_buf)
        output_buf.seek(0)
        final_bytes = output_buf.read()

    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

    filename = f"{data.name.replace(' ', '_')}_Resume.pdf"
    return StreamingResponse(
        io.BytesIO(final_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(final_bytes)),
        },
    )


# get all resume route
@resumeRouter.get("/get_resume", response_model=GetResumeResponse)
def get(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return get_all_resume(db, current_user)


# get resume by id route
@resumeRouter.get("/get_resume/{id}", response_model=GetResumeResponse)
def get(
    db: Session = Depends(get_db),
    id: int = None,
    current_user: dict = Depends(get_current_user),
):
    return get_resume_by_id(db, id, current_user)


# update resume route
@resumeRouter.put("/update/{resume_id}", response_model=GetResumeResponse)
def update(
    resume_id: int,
    data: Resume_Validation,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return update_resume(db, resume_id, data, current_user)


# delete resume route
@resumeRouter.delete("/delete/{resume_id}")
def delete(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return delete_resume(db, resume_id, current_user)


# @resumeRouter.post("/create", response_model=GetResumeResponse)
# def create(resume: Resume_Validation, db: Session = Depends(get_db)):
#     return create_resume(db, resume)


@resumeRouter.get("/get")
def create(db: Session = Depends(get_db)):
    return get_resume(db)
