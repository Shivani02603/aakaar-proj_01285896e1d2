from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from pydantic import BaseModel, Field
from database.models import ChatSession, ChatMessage
from database.config import get_db
from backend.services.auth import get_current_user
from datetime import datetime

router = APIRouter(tags=["Chat History"])

# Pydantic Schemas
class ChatSessionBase(BaseModel):
    title: str = Field(..., example="My Chat Session")

class ChatSessionCreate(ChatSessionBase):
    document_id: UUID = Field(..., example="123e4567-e89b-12d3-a456-426614174000")

class ChatSessionResponse(ChatSessionBase):
    id: UUID
    user_id: UUID
    document_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ChatMessageBase(BaseModel):
    role: str = Field(..., example="user")
    content: str = Field(..., example="Hello, how are you?")
    chunk_ids: List[UUID] = Field(default=[], example=["123e4567-e89b-12d3-a456-426614174000"])

class ChatMessageCreate(ChatMessageBase):
    pass

class ChatMessageResponse(ChatMessageBase):
    id: UUID
    session_id: UUID
    created_at: datetime

    class Config:
        orm_mode = True

# Routes
@router.post("/chat/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_session(
    session_data: ChatSessionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    new_session = ChatSession(
        user_id=current_user["id"],
        document_id=session_data.document_id,
        title=session_data.title,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

@router.get("/chat/sessions", response_model=List[ChatSessionResponse])
async def list_chat_sessions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    sessions = db.query(ChatSession).filter(ChatSession.user_id == current_user["id"]).all()
    return sessions

@router.get("/chat/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_chat_messages(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user["id"]).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).all()
    return messages

@router.delete("/chat/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user["id"]).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    db.delete(session)
    db.commit()
    return None