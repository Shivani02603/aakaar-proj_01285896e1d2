from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from pydantic import BaseModel, Field
from database.models import DocumentChunk
from database.config import get_db
from backend.services.auth import get_current_user
from ai.rag import retrieve_context, answer_question

router = APIRouter(tags=["Question Answering"])

# Pydantic Schemas
class ChunkCitation(BaseModel):
    chunk_id: UUID
    content: str
    metadata: dict

class AnswerResponse(BaseModel):
    answer: str
    citations: List[ChunkCitation]

class QueryRequest(BaseModel):
    query: str

# Endpoint: POST /question-answering/query
@router.post("/question-answering/query", response_model=AnswerResponse, status_code=status.HTTP_200_OK)
async def query_question_answering(
    request: QueryRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Accepts a user query, retrieves the top-5 most relevant chunks, and generates an answer with citations.
    """
    try:
        # Retrieve top-5 relevant chunks
        relevant_chunks = await retrieve_context(
            query=request.query,
            top_k=5,
            session_id=None,  # No session ID for standalone queries
            user_id=current_user["id"],
        )

        if not relevant_chunks:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No relevant chunks found for the query.",
            )

        # Generate answer using LLM
        answer_data = await answer_question(
            query=request.query,
            session_id=None,  # No session ID for standalone queries
            user_id=current_user["id"],
        )

        # Prepare citations
        citations = [
            ChunkCitation(
                chunk_id=chunk["id"],
                content=chunk["content"],
                metadata=chunk["metadata"],
            )
            for chunk in relevant_chunks
        ]

        return AnswerResponse(answer=answer_data["answer"], citations=citations)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the query.",
        )