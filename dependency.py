# dependencies.py
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
