from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dependency import get_db
from schemas import (
    UserCreate,
    UserResponse,
    UserRegsiterResponse,
    UserLoginResponse,
    UserUpdate,
    GetUserResponse,
)
from modules.user.user_service import (
    create_user,
    get_all_users,
    get_single_users,
    oauth_login_service,
    update_single_user,
    delete_user,
    login_user,
    get_current_user,
    get_user_list,
)

router = APIRouter(tags=["user"], prefix="/user")


@router.post("/create", response_model=UserRegsiterResponse)
def create(user: UserCreate, db: Session = Depends(get_db)):
    return create_user(db, user)


@router.post("/login", response_model=UserLoginResponse)
def create(user: dict, db: Session = Depends(get_db)):
    return login_user(db, user)


@router.get("/get", response_model=GetUserResponse)
def get_all(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return get_all_users(db, current_user)


@router.get("/getall", response_model=GetUserResponse)
def get_all(
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    try:
        return get_user_list(db, current_user)
    except Exception as e:
        print("error message", e)
        raise HTTPException(
            status_code=500,
            detail="An internal server error occurred. Please try again later.",
        )


@router.get("/get/{user_id}", response_model=UserResponse)
def get_all(user_id: int, db: Session = Depends(get_db)):
    return get_single_users(db, user_id)


@router.put("/update", response_model=UserRegsiterResponse)
def update_user(user: UserUpdate, db: Session = Depends(get_db)):
    return update_single_user(db, user)


@router.delete("/delete", response_model=UserRegsiterResponse)
def update_user(user: UserUpdate, db: Session = Depends(get_db)):
    return delete_user(db, user)


@router.post("/oauth_login", status_code=201)
def oauth_login(payload: UserCreate, db: Session = Depends(get_db)):
    try:
        return oauth_login_service(db, payload)
    except Exception as e:
        print("error message", e)
        raise HTTPException(
            status_code=500,
            detail="An internal server error occurred. Please try again later.",
        )
