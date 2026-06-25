import uuid
from typing import List, Optional

from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from database.models import ChatSession, ChatMessage
from database.config import get_db


class ChatHistoryService:
    def create_chat_session(self, session_data: dict, db: Session, user_id: uuid.UUID) -> ChatSession:
        try:
            new_session = ChatSession(
                id=uuid.uuid4(),
                user_id=user_id,
                document_id=session_data.get("document_id"),
                title=session_data.get("title"),
                created_at=session_data.get("created_at"),
                updated_at=session_data.get("updated_at"),
            )
            db.add(new_session)
            db.commit()
            db.refresh(new_session)
            return new_session
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error creating chat session: {str(e)}")

    def get_chat_session_by_id(self, session_id: uuid.UUID, db: Session, user_id: uuid.UUID) -> ChatSession:
        session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        return session

    def list_chat_sessions(self, db: Session, user_id: uuid.UUID) -> List[ChatSession]:
        try:
            sessions = db.query(ChatSession).filter(ChatSession.user_id == user_id).all()
            return sessions
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Error listing chat sessions: {str(e)}")

    def update_chat_session(self, session_id: uuid.UUID, session_data: dict, db: Session, user_id: uuid.UUID) -> ChatSession:
        session = self.get_chat_session_by_id(session_id, db, user_id)
        try:
            session.title = session_data.get("title", session.title)
            session.updated_at = session_data.get("updated_at", session.updated_at)
            db.commit()
            db.refresh(session)
            return session
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error updating chat session: {str(e)}")

    def delete_chat_session(self, session_id: uuid.UUID, db: Session, user_id: uuid.UUID) -> None:
        session = self.get_chat_session_by_id(session_id, db, user_id)
        try:
            db.delete(session)
            db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error deleting chat session: {str(e)}")

    def create_chat_message(self, message_data: dict, db: Session, session_id: uuid.UUID, user_id: uuid.UUID) -> ChatMessage:
        session = self.get_chat_session_by_id(session_id, db, user_id)
        try:
            new_message = ChatMessage(
                id=uuid.uuid4(),
                session_id=session.id,
                role=message_data.get("role"),
                content=message_data.get("content"),
                chunk_ids=message_data.get("chunk_ids"),
                created_at=message_data.get("created_at"),
            )
            db.add(new_message)
            db.commit()
            db.refresh(new_message)
            return new_message
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error creating chat message: {str(e)}")

    def get_chat_messages_by_session_id(self, session_id: uuid.UUID, db: Session, user_id: uuid.UUID) -> List[ChatMessage]:
        session = self.get_chat_session_by_id(session_id, db, user_id)
        try:
            messages = db.query(ChatMessage).filter(ChatMessage.session_id == session.id).all()
            return messages
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving chat messages: {str(e)}")

    def delete_chat_message(self, message_id: uuid.UUID, db: Session, user_id: uuid.UUID) -> None:
        message = db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
        if not message:
            raise HTTPException(status_code=404, detail="Chat message not found")
        try:
            db.delete(message)
            db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error deleting chat message: {str(e)}")