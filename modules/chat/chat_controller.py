from unittest import result

from fastapi import (
    FastAPI,
    File,
    UploadFile,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    APIRouter,
    Depends,
    Form,
)
from flask import json
from sqlalchemy.orm import Session
from sqlalchemy import text
from dependency import get_db
from openai import OpenAI
import os
from PyPDF2 import PdfReader
from docx import Document
from fastapi import UploadFile
import io
from .connection_manager import ConnectionManager
from modules.user.user_service import get_current_user
from .chat_model import MessageHistory
from database import SessionLocal
import httpx
import pdfplumber
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
import easyocr
from pdf2image import convert_from_bytes

manager = ConnectionManager()
chatRouter = APIRouter(tags=["chat"], prefix="/chat")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # store in .env or secrets
OCR_API_KEY = os.getenv("OCR_API_KEY")  # Replace with your actual OCR API key
OCR_API_URL = os.getenv("OCR_API_URL")  # Replace with your actual OCR API endpoint
GROQ_MODEL = os.getenv("GROQ_MODEL")  # Default to a specific model
GROQ_API_URL = os.getenv("GROQ_API_URL")


# # websocket endpoint
# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await manager.connect(websocket)
#     try:
#         while True:
#             data = await websocket.receive_json()
#             await manager.broadcast({"type": "message", "data": data}, websocket)
#     except WebSocketDisconnect:
#         manager.disconnect(websocket)


# generate conversation id
# def get_conversation_id(user1: str, user2: str) -> str:
#     return "-".join(sorted([user1, user2]))
def save_message(db, sender_id, receiver_id, text, file_url=None, message_type="text"):
    conversation_id = "_".join(sorted([str(sender_id), str(receiver_id)]))

    msg = MessageHistory(
        conversation_id=conversation_id,
        sender_id=sender_id,
        receiver_id=receiver_id,
        message=text,
        message_type=message_type,
        file_url=file_url,
        status="sent",
    )

    db.add(msg)
    db.commit()
    db.refresh(msg)

    return msg


# websocket private message endpoint
@chatRouter.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print("WebSocket connection attempt", websocket.query_params.get("token"))
    db = SessionLocal()
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)  # Policy Violation
        return
    current_user = get_current_user(token)
    user_id = current_user.get("id") or current_user.get("user_id")
    try:
        print("Authenticated user:", user_id)
        await manager.connect(user_id, websocket)

    except HTTPException as e:
        print("Authentication failed:", e.detail)
        await websocket.close(code=1008)  # Policy Violation
        return
    try:
        while True:
            data = await websocket.receive_json()
            # await manager.broadcast({"type": "message", "data": data}, websocket)
            receiver_id = data["to"]
            print("Sending message to:", receiver_id)
            print("from user:", user_id)
            message = {"from": user_id, "text": data["text"]}

            # save message to database
            # ✅ Save message to database
            saved_message = save_message(
                db=db,
                sender_id=user_id,
                receiver_id=receiver_id,
                text=data["text"],
                file_url=data.get("img_url"),
                message_type=data.get("type"),
            )

            # convert to JSON response message payload
            message_payload = {
                "id": str(saved_message.id),
                "conversation_id": saved_message.conversation_id,
                "sender_id": saved_message.sender_id,
                "receiver_id": saved_message.receiver_id,
                "message": saved_message.message,
                "message_type": saved_message.message_type,
                "file_url": saved_message.file_url,
                "status": saved_message.status,
                "created_at": saved_message.created_at.isoformat(),
            }

            # send private message to receiver
            await manager.send_private_message(receiver_id, message_payload)

            await manager.send_private_message(
                user_id, message_payload
            )  # Echo back to sender
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)


@chatRouter.get("/history")
async def get_chat_history(
    with_user_id: str, current_user: dict = Depends(get_current_user)
):
    db = SessionLocal()
    try:
        user_id = current_user.get("id") or current_user.get("user_id")
    except HTTPException as e:
        print("Authentication failed:", e.detail)
        raise HTTPException(status_code=401, detail="Unauthorized")

    conversation_id = "_".join(sorted([str(user_id), str(with_user_id)]))
    messages = (
        db.query(MessageHistory)
        .filter(MessageHistory.conversation_id == conversation_id)
        .order_by(MessageHistory.created_at.asc())
        .all()
    )
    return [
        {
            "id": str(msg.id),
            "conversation_id": msg.conversation_id,
            "sender_id": msg.sender_id,
            "receiver_id": msg.receiver_id,
            "message": msg.message,
            "message_type": msg.message_type,
            "file_url": msg.file_url,
            "status": msg.status,
            "created_at": msg.created_at.isoformat(),
        }
        for msg in messages
    ]


@chatRouter.get("/chat-list")
def get_chat_list(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
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
            file_url,
            created_at
        FROM message_history
        WHERE sender_id = :user_id OR receiver_id = :user_id
        ORDER BY conversation_id, created_at DESC;
    """)

    result = db.execute(query, {"user_id": str(user_id)}).fetchall()

    return [dict(row._mapping) for row in result]
