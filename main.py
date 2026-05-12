from fastapi import (
    FastAPI,
    File,
    UploadFile,
    HTTPException,
)
from fastapi.middleware.cors import CORSMiddleware
from modules.user import user_controller
from modules.order import order_controller
from modules.resume import resume_controller
from modules.chat import chat_controller
from modules.resume.ai_resume_controller import ai_resume_router
from config import origin
import os
from database import engine, Base
import cloudinary.uploader

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)

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

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_TYPES = ["image/jpeg", "image/png", "image/jpg", "application/pdf"]


# keep alive api


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # ✅ Validate file type
        if file.content_type not in ALLOWED_TYPES:
            raise HTTPException(
                status_code=400, detail="Only images and PDFs are allowed"
            )

        # ✅ Upload directly to Cloudinary (no local storage)
        file.file.seek(0)

        upload_result = cloudinary.uploader.upload(
            file.file,
            folder="uploads",
            resource_type="auto",
            type="upload",  # 🔥 IMPORTANT
        )

        return {
            "success": True,
            "message": "File uploaded successfully",
            "fileUrl": upload_result.get("secure_url"),
            "public_id": upload_result.get("public_id"),
            "fileType": upload_result.get("resource_type"),
        }

    except HTTPException as http_err:
        # Known validation errors
        raise http_err

    except Exception as e:
        # Unexpected errors (Cloudinary, network, etc.)
        print("Upload Error:", str(e))
        raise HTTPException(status_code=500, detail="File upload failed")


# Routes
app.include_router(user_controller.router)
app.include_router(order_controller.orderRouter)
app.include_router(resume_controller.resumeRouter)
app.include_router(chat_controller.chatRouter)
app.include_router(ai_resume_router)
