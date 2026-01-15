from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from modules.user import user_controller
from modules.order import order_controller
from modules.resume import resume_controller
from config import origin
import os
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import modules
import shutil
from database import engine, Base

app = FastAPI()

Base.metadata.create_all(bind=engine)  # Create tables if not exists

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origin,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_TYPES = ["image/jpeg", "image/png", "image/jpg", "application/pdf"]


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only images and PDFs are allowed")

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    print(file_path)
    print(file.file)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "success": True,
        "message": "File uploaded successfully",
        "filename": file.filename,
    }


# Routes
app.include_router(user_controller.router)
app.include_router(order_controller.orderRouter)
app.include_router(resume_controller.resumeRouter)
