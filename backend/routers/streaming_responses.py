from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from pydantic import BaseModel, Field
from database.models import ChatMessage, ChatSession
from database.config import get_db
from backend.services.auth import get_current_user
from ai.streaming import stream_answer

router = APIRouter(tags=["Streaming Responses"])

# Pydantic Schemas
class StreamAnswerRequest(BaseModel):
    query: str = Field(..., description="The query to be answered.")
    session_id: UUID = Field(..., description="The ID of the chat session.")

class StreamAnswerResponse(BaseModel):
    tokens: List[str] = Field(..., description="List of tokens generated as the answer.")

# Endpoint to stream answer tokens
@router.post("/stream/answer", response_model=None, status_code=status.HTTP_200_OK)
async def stream_answer_endpoint(
    request: StreamAnswerRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Stream answer tokens to the frontend in real-time.
    """
    try:
        # Validate session existence
        session = db.query(ChatSession).filter(ChatSession.id == request.session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found."
            )
        if session.user_id != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this chat session."
            )

        # Stream the answer tokens
        async def token_generator():
            async for token in stream_answer(request.query, str(request.session_id), str(current_user["id"])):
                yield f"{token}\n"

        return StreamingResponse(token_generator(), media_type="text/plain")

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while streaming the answer."
        )