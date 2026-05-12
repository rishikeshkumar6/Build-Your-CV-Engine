from sqlalchemy.orm import Session, load_only
from fastapi import HTTPException, Depends
from modules import User
from psycopg2 import DatabaseError as DataBaseError
from schemas import UserCreate, UserUpdate
from dependency import oauth2_scheme
from sqlalchemy import or_, text
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
            full_name=user.full_name,
            email=user.email,
            password=hash_password(user.password),
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        return {"message": "user created successfully", "statusCode": 201}
    except HTTPException:
        raise
    except DataBaseError as db_err:
        print("database error", db_err)
        raise HTTPException(
            status_code=500, detail="An error occurred while creating the user: "
        )
    except Exception as e:
        print("error message", e)
        raise HTTPException(
            status_code=500,
            detail="An internal server error occurred. Please try again later.",
        )


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
        client_id = current_user.get("id") or current_user.get("user_id")
        query = (
            db.query(User.id, User.email, User.full_name, User.uuid)
            .filter(User.id == client_id)
            .first()
        )
        if not query:
            raise HTTPException(status_code=404, detail="no users found")

        data = {
            "id": query.id,
            "email": query.email,
            "full_name": query.full_name,
            "uuid": query.uuid,
        }
        return {"statusCode": 200, "data": data, "status": True}

    except DataBaseError as db_err:
        print("database error", db_err)
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        print("error message", e)
        raise HTTPException(status_code=500, detail=str(e))


def get_chat_list(
    db: Session,
    current_user: dict,
):
    user_id = current_user.get("id") or current_user.get("user_id")

    query = text("""
        SELECT DISTINCT ON (conversation_id)
            conversation_id,

            CASE
                WHEN sender_id = :user_id THEN receiver_id
                ELSE sender_id
            END AS other_user_id,

            message,
            created_at
        FROM message_history
        WHERE sender_id = :user_id OR receiver_id = :user_id
        ORDER BY conversation_id, created_at DESC;
    """)

    result = db.execute(query, {"user_id": str(user_id)}).fetchall()

    return [dict(row._mapping) for row in result]


def get_user_list(db: Session, current_user: dict):
    try:
        client_id = current_user.get("id") or current_user.get("user_id")
        print("client id---->", client_id)
        user_last_message_list = get_chat_list(db, current_user)
        print("user_last_message_list", user_last_message_list)
        query = db.query(User.id, User.email, User.full_name, User.uuid).all()
        if not query:
            raise HTTPException(status_code=404, detail="no users found")

        data = [
            {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "uuid": user.uuid,
                "last_message": next(
                    (
                        msg["message"]
                        for msg in user_last_message_list
                        if str(user.id) in msg["other_user_id"]
                    ),
                    None,
                ),
            }
            for user in query
        ]
        print("data---->", data)
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


def oauth_login_service(db: Session, payload: UserCreate):
    try:
        # check if user already exists
        existing_user = db.query(User).filter(User.email == payload.email).first()

        # if user exists → login
        if existing_user:
            token = create_access_token(
                data={
                    "id": existing_user.id,
                    "email": existing_user.email,
                }
            )

            return {
                "statusCode": 200,
                "message": "Login successful",
                "token": token,
                "user": {
                    "id": existing_user.id,
                    "email": existing_user.email,
                    "full_name": existing_user.full_name,
                    "auth_provider": existing_user.auth_provider,
                },
            }

        # create new user
        new_user = User(
            email=payload.email,
            full_name=payload.full_name,
            auth_provider=payload.auth_provider,
            password=None,
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # generate token
        token = create_access_token(
            data={
                "id": new_user.id,
                "email": new_user.email,
            }
        )

        return {
            "statusCode": 201,
            "message": "User created successfully",
            "token": token,
            "user": {
                "id": new_user.id,
                "email": new_user.email,
                "full_name": new_user.full_name,
                "auth_provider": new_user.auth_provider,
            },
        }

    except Exception as e:
        print("OAuth Login Error:", e)

        raise HTTPException(
            status_code=500,
            detail="Something went wrong during OAuth login",
        )
