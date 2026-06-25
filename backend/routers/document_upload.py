from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from pydantic import BaseModel, Field
from database.models import Document
from database.config import get_db
from backend.services.auth import get_current_user
from backend.services.document_upload_service import DocumentUploadService

router = APIRouter(tags=["Document Upload"])

# Pydantic Schemas
class DocumentBase(BaseModel):
    filename: str
    file_size: int
    status: str
    uploaded_at: str
    processed_at: str | None = None

class DocumentCreate(BaseModel):
    filename: str = Field(..., example="example.pdf")
    file_size: int = Field(..., example=1024)
    status: str = Field(..., example="uploaded")

class DocumentResponse(DocumentBase):
    id: UUID
    user_id: UUID

# Routes
@router.post("/documents/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload a PDF document.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed."
        )

    try:
        document_service = DocumentUploadService()
        document = await document_service.upload_file(file, db, current_user)
        return document
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while uploading the document."
        )

@router.get("/documents", response_model=List[DocumentResponse], status_code=status.HTTP_200_OK)
async def list_documents(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    List all documents for the authenticated user.
    """
    try:
        document_service = DocumentUploadService()
        documents = await document_service.list_documents(db, current_user)
        return documents
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving documents."
        )

@router.get("/documents/{document_id}", response_model=DocumentResponse, status_code=status.HTTP_200_OK)
async def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Retrieve a specific document by ID.
    """
    try:
        document_service = DocumentUploadService()
        document = await document_service.get_document_by_id(document_id, db, current_user)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found."
            )
        return document
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the document."
        )

@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Delete a specific document by ID.
    """
    try:
        document_service = DocumentUploadService()
        await document_service.delete_document(document_id, db, current_user)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the document."
        )