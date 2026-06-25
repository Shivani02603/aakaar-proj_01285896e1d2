import uuid
from typing import List, Optional

from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from database.models import ChatMessage, DocumentChunk
from database.config import get_db
from ai.rag import retrieve_context, answer_question


class QuestionAnsweringService:
    def create_chat_message(
        self, session_id: uuid.UUID, role: str, content: str, chunk_ids: List[uuid.UUID], db: Session = Depends(get_db)
    ) -> ChatMessage:
        try:
            chat_message = ChatMessage(
                session_id=session_id,
                role=role,
                content=content,
                chunk_ids=chunk_ids,
                created_at=datetime.utcnow(),
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
        chat_messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).all()
        return chat_messages

    def update_chat_message(
        self, message_id: uuid.UUID, updated_content: str, db: Session = Depends(get_db)
    ) -> ChatMessage:
        chat_message = db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
        if not chat_message:
            raise HTTPException(status_code=404, detail="Chat message not found")
        try:
            chat_message.content = updated_content
            chat_message.updated_at = datetime.utcnow()
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

    def generate_answer_with_citations(
        self, query: str, session_id: uuid.UUID, user_id: uuid.UUID, db: Session = Depends(get_db)
    ) -> dict:
        try:
            # Retrieve top-5 relevant chunks using the RAG pipeline
            relevant_chunks = retrieve_context(query=query, top_k=5, session_id=session_id, user_id=user_id)

            if not relevant_chunks:
                raise HTTPException(status_code=404, detail="No relevant chunks found for the query")

            # Extract content from chunks for the LLM
            chunk_texts = [chunk["content"] for chunk in relevant_chunks]

            # Generate answer using the LLM
            answer = answer_question(query=query, session_id=session_id, user_id=user_id)

            # Prepare citations
            citations = [{"chunk_id": chunk["id"], "content": chunk["content"]} for chunk in relevant_chunks]

            return {
                "answer": answer,
                "citations": citations,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate answer: {str(e)}")