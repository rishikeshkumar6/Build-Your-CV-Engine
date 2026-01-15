from sqlalchemy.orm import Session, joinedload, load_only
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from modules import User, Order, Resume
from psycopg2 import DatabaseError as DataBaseError
from schemas import UserCreate, UserUpdate
from dependency import oauth2_scheme
from modules.user.user_controller import oauth2_scheme
from sqlalchemy import or_
from auth import (
    hash_password,
    create_access_token,
    verify_password,
    decode_access_token,
)


def create_user(db: Session, user: UserCreate):
    try:
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            raise HTTPException(
                status_code=409,
                detail="User with this email already exists",
            )

        db_user = User(
            email=user.email,
            password=hash_password(user.password),
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        return {"message": "user created successfully", "statusCode": 201}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def to_dict(model):
    return {
        column.name: getattr(model, column.name) for column in model.__table__.columns
    }


def login_user(db: Session, user: dict):
    query = (
        db.query(User)
        .options(load_only(User.id, User.email, User.password))
        .filter(User.email == user["email"])
        .first()
    )

    if not query or not verify_password(user["password"], query.password):
        raise HTTPException(status_code=404, detail="User not found")

    token = create_access_token({"email": query.email, "id": query.id})

    return {"token": token, "statusCode": 201}


def get_current_user(token: str = Depends(oauth2_scheme)):
    print("token----->", token)
    response = decode_access_token(token)
    print("response checking---->", response)
    if response:
        return response


def get_all_users(db: Session, current_user: dict):
    try:
        client_id = current_user.get("id")
        query = (
            db.query(User.id, User.email, User.uuid)
            .filter(User.id == client_id)
            .first()
        )
        if not query:
            raise HTTPException(status_code=404, detail="no users found")

        data = {"id": query.id, "email": query.email, "uuid": query.uuid}
        return {"statusCode": 200, "data": data, "status": True}

    except DataBaseError as db_err:
        print("database error", db_err)
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        print("error message", e)
        raise HTTPException(status_code=500, detail=str(e))


def get_single_users(db: Session, user_id: int):
    try:
        query = db.query(User).filter(User.id == user_id).first()
        return query
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def update_single_user(db: Session, user: UserUpdate):
    try:
        query = db.query(User).filter(User.id == user.id).first()
        if not query:
            raise HTTPException(status_code=401, detail="user not found")
        query.email = user.email
        db.commit()
        db.refresh(query)
        return {"message": "user updated successfully", "statusCode": 201}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def delete_user(db: Session, user: UserUpdate):
    try:
        query = db.query(User).filter(User.id == user.id).first()
        if not query:
            raise HTTPException(status_code=401, detail="user not found")
        db.delete(query)
        db.commit()
        return {"message": "user updated successfully", "statusCode": 201}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
