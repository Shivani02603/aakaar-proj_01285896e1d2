import uuid
from typing import List, Optional

from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from database.models import ChatMessage
from database.config import get_db
from ai.streaming import stream_answer


class StreamingResponsesService:
    def create_chat_message(
        self, session_id: uuid.UUID, role: str, content: str, chunk_ids: List[uuid.UUID], db: Session = Depends(get_db)
    ) -> ChatMessage:
        try:
            chat_message = ChatMessage(
                session_id=session_id,
                role=role,
                content=content,
                chunk_ids=chunk_ids,
            )
            db.add(chat_message)
            db.commit()
            db.refresh(chat_message)
            return chat_message
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create chat message: {str(e)}")

    def get_chat_message_by_id(self, message_id: uuid.UUID, db: Session = Depends(get_db)) -> ChatMessage:
        chat_message = db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
        if not chat_message:
            raise HTTPException(status_code=404, detail="Chat message not found")
        return chat_message

    def list_all_chat_messages(self, session_id: uuid.UUID, db: Session = Depends(get_db)) -> List[ChatMessage]:
        try:
            chat_messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).all()
            return chat_messages
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Failed to list chat messages: {str(e)}")

    def update_chat_message(
        self, message_id: uuid.UUID, content: Optional[str] = None, db: Session = Depends(get_db)
    ) -> ChatMessage:
        chat_message = db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
        if not chat_message:
            raise HTTPException(status_code=404, detail="Chat message not found")

        try:
            if content:
                chat_message.content = content
            db.commit()
            db.refresh(chat_message)
            return chat_message
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update chat message: {str(e)}")

    def delete_chat_message(self, message_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
        chat_message = db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
        if not chat_message:
            raise HTTPException(status_code=404, detail="Chat message not found")

        try:
            db.delete(chat_message)
            db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete chat message: {str(e)}")

    def stream_answer(
        self, query: str, session_id: uuid.UUID, user_id: uuid.UUID, db: Session = Depends(get_db)
    ) -> str:
        try:
            # Stream the answer tokens in real-time
            answer_tokens = stream_answer(query, session_id, user_id)
            return answer_tokens
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to stream answer: {str(e)}")