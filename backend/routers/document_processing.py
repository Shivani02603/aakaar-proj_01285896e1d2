from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from pydantic import BaseModel, Field
from database.models import Document
from database.config import get_db
from backend.services.auth import get_current_user
from backend.services.document_processing_service import DocumentProcessingService
from ai.ingest import chunk
from ai.embeddings import embed_batch

router = APIRouter(tags=["Document Processing"])

# Pydantic Schemas
class DocumentBase(BaseModel):
    filename: str
    file_size: int
    status: str
    uploaded_at: str
    processed_at: str | None = None

class DocumentCreate(BaseModel):
    filename: str
    file_size: int

class DocumentResponse(DocumentBase):
    id: UUID
    user_id: UUID

class DocumentUpdate(BaseModel):
    status: str
    processed_at: str | None = None

# Route Handlers
@router.post("/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        # Save document metadata
        document_service = DocumentProcessingService(db)
        document = await document_service.create_document(file, current_user)
        
        # Extract text from PDF
        pdf_content = await file.read()
        text = pdf_content.decode("utf-8")  # Assuming UTF-8 encoding for simplicity
        
        # Chunk the text
        chunks = chunk(text, chunk_size=1000, chunk_overlap=200)
        
        # Generate embeddings
        embeddings = embed_batch([chunk["content"] for chunk in chunks])
        
        # Save chunks and embeddings
        for i, chunk_data in enumerate(chunks):
            chunk_data["embedding"] = embeddings[i]
            await document_service.create_document_chunk(chunk_data, document.id, current_user)
        
        # Update document status
        await document_service.update_document_status(document.id, "processed")
        
        return document
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents", response_model=List[DocumentResponse], status_code=status.HTTP_200_OK)
async def list_documents(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        document_service = DocumentProcessingService(db)
        documents = await document_service.list_all_documents(current_user)
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{document_id}", response_model=DocumentResponse, status_code=status.HTTP_200_OK)
async def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        document_service = DocumentProcessingService(db)
        document = await document_service.get_document_by_id(document_id, current_user)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/documents/{document_id}", response_model=DocumentResponse, status_code=status.HTTP_200_OK)
async def update_document(
    document_id: UUID,
    document_data: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        document_service = DocumentProcessingService(db)
        updated_document = await document_service.update_document(document_id, document_data, current_user)
        if not updated_document:
            raise HTTPException(status_code=404, detail="Document not found")
        return updated_document
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        document_service = DocumentProcessingService(db)
        success = await document_service.delete_document(document_id, current_user)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))