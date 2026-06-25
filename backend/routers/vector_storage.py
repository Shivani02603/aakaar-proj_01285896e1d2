from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from pydantic import BaseModel, Field
from database.models import DocumentChunk
from database.config import get_db
from backend.services.auth import get_current_user
from backend.services.vector_storage_service import (
    create_chunk,
    get_chunk_by_id,
    list_all_chunks,
    update_chunk,
    delete_chunk,
)

router = APIRouter(tags=["Vector Storage"])


# Pydantic Schemas
class DocumentChunkBase(BaseModel):
    document_id: UUID
    chunk_index: int
    content: str
    embedding: List[float]
    metadata: dict


class DocumentChunkCreate(DocumentChunkBase):
    pass


class DocumentChunkUpdate(BaseModel):
    content: str | None = None
    embedding: List[float] | None = None
    metadata: dict | None = None


class DocumentChunkResponse(DocumentChunkBase):
    id: UUID

    class Config:
        orm_mode = True


# Routes
@router.get("/chunks", response_model=List[DocumentChunkResponse])
async def list_document_chunks(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    List all document chunks for the authenticated user.
    """
    chunks = list_all_chunks(db, current_user)
    return chunks


@router.get("/chunks/{chunk_id}", response_model=DocumentChunkResponse)
async def get_document_chunk(
    chunk_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Retrieve a specific document chunk by ID.
    """
    chunk = get_chunk_by_id(chunk_id, db, current_user)
    if not chunk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document chunk not found"
        )
    return chunk


@router.post("/chunks", response_model=DocumentChunkResponse, status_code=status.HTTP_201_CREATED)
async def create_document_chunk(
    chunk_data: DocumentChunkCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Create a new document chunk.
    """
    chunk = create_chunk(chunk_data, db, current_user)
    return chunk


@router.put("/chunks/{chunk_id}", response_model=DocumentChunkResponse)
async def update_document_chunk(
    chunk_id: UUID,
    chunk_update: DocumentChunkUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Update an existing document chunk.
    """
    chunk = update_chunk(chunk_id, chunk_update, db, current_user)
    if not chunk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document chunk not found"
        )
    return chunk


@router.delete("/chunks/{chunk_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document_chunk(
    chunk_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Delete a document chunk by ID.
    """
    success = delete_chunk(chunk_id, db, current_user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document chunk not found"
        )