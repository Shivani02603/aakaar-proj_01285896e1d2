import os
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, UploadFile, Depends
from sqlalchemy.orm import Session
from database.models import Document, User
from database.config import get_db


class DocumentUploadService:
    def __init__(self, db: Session):
        self.db = db

    def create_document(self, user_id: uuid.UUID, file: UploadFile) -> Document:
        """
        Create a new document entry in the database and save the uploaded file.
        """
        try:
            # Validate file type
            if not file.filename.endswith(".pdf"):
                raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

            # Generate unique filename
            unique_filename = f"{uuid.uuid4()}_{file.filename}"

            # Save file to disk
            upload_dir = "uploads"
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, unique_filename)
            with open(file_path, "wb") as f:
                f.write(file.file.read())

            # Create document entry
            document = Document(
                id=uuid.uuid4(),
                user_id=user_id,
                filename=file.filename,
                file_size=os.path.getsize(file_path),
                status="uploaded",
                uploaded_at=datetime.utcnow(),
                processed_at=None,
            )
            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)

            return document
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")

    def get_document_by_id(self, document_id: uuid.UUID, user_id: uuid.UUID) -> Document:
        """
        Retrieve a document by its ID.
        """
        document = self.db.query(Document).filter(Document.id == document_id, Document.user_id == user_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found.")
        return document

    def list_documents(self, user_id: uuid.UUID) -> List[Document]:
        """
        List all documents for a specific user.
        """
        documents = self.db.query(Document).filter(Document.user_id == user_id).all()
        return documents

    def update_document_status(self, document_id: uuid.UUID, user_id: uuid.UUID, status: str) -> Document:
        """
        Update the status of a document.
        """
        document = self.get_document_by_id(document_id, user_id)
        document.status = status
        document.processed_at = datetime.utcnow() if status == "processed" else None
        self.db.commit()
        self.db.refresh(document)
        return document

    def delete_document(self, document_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """
        Delete a document by its ID.
        """
        document = self.get_document_by_id(document_id, user_id)
        self.db.delete(document)
        self.db.commit()