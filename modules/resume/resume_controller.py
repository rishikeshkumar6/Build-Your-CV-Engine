from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from dependency import get_db
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
