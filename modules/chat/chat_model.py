import uuid
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from database import Base


class MessageHistory(Base):
    __tablename__ = "message_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    conversation_id = Column(String, index=True, nullable=False)

    sender_id = Column(String, index=True, nullable=False)
    receiver_id = Column(String, index=True, nullable=False)

    message = Column(Text, nullable=True)

    message_type = Column(String, default="text")
    status = Column(String, default="sent")
    file_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
