import os
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, Depends, UploadFile
from sqlalchemy.orm import Session
from database.models import Document, User, DocumentChunk
from database.config import get_db
from ai.embeddings import embed_batch
from ai.ingest import chunk


class DocumentProcessingService:
    def create_document(self, file: UploadFile, user_id: uuid.UUID, db: Session) -> Document:
        try:
            # Validate file type
            if not file.filename.endswith(".pdf"):
                raise HTTPException(status_code=400, detail="Only PDF files are supported.")

            # Generate unique ID for the document
            document_id = uuid.uuid4()

            # Save the file to the server
            upload_dir = os.getenv("UPLOAD_DIR", "uploads")
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, f"{document_id}.pdf")
            with open(file_path, "wb") as f:
                f.write(file.file.read())

            # Create document record
            document = Document(
                id=document_id,
                user_id=user_id,
                filename=file.filename,
                file_size=os.path.getsize(file_path),
                status="uploaded",
                uploaded_at=datetime.utcnow(),
                processed_at=None,
            )
            db.add(document)
            db.commit()
            db.refresh(document)

            return document
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")

    def get_document_by_id(self, document_id: uuid.UUID, db: Session) -> Document:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found.")
        return document

    def list_all_documents(self, user_id: uuid.UUID, db: Session) -> List[Document]:
        documents = db.query(Document).filter(Document.user_id == user_id).all()
        return documents

    def update_document_status(self, document_id: uuid.UUID, status: str, db: Session) -> Document:
        document = self.get_document_by_id(document_id, db)
        document.status = status
        db.commit()
        db.refresh(document)
        return document

    def delete_document(self, document_id: uuid.UUID, db: Session) -> None:
        document = self.get_document_by_id(document_id, db)
        db.delete(document)
        db.commit()

    def process_document(self, document_id: uuid.UUID, db: Session) -> List[DocumentChunk]:
        try:
            # Retrieve the document
            document = self.get_document_by_id(document_id, db)
            if document.status != "uploaded":
                raise HTTPException(status_code=400, detail="Document is not in 'uploaded' status.")

            # Load the PDF file
            upload_dir = os.getenv("UPLOAD_DIR", "uploads")
            file_path = os.path.join(upload_dir, f"{document.id}.pdf")
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail="Uploaded file not found.")

            # Extract text from the PDF
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            text = "".join(page.extract_text() for page in reader.pages)

            # Split text into chunks
            chunks = chunk(text, chunk_size=1000, chunk_overlap=200)

            # Generate embeddings for each chunk
            embeddings = embed_batch([chunk["content"] for chunk in chunks])

            # Create DocumentChunk records
            document_chunks = []
            for index, (chunk_data, embedding) in enumerate(zip(chunks, embeddings)):
                document_chunk = DocumentChunk(
                    id=uuid.uuid4(),
                    document_id=document.id,
                    chunk_index=index,
                    content=chunk_data["content"],
                    embedding=embedding,
                    metadata=chunk_data["metadata"],
                )
                db.add(document_chunk)
                document_chunks.append(document_chunk)

            # Update document status
            document.status = "processed"
            document.processed_at = datetime.utcnow()
            db.commit()

            return document_chunks
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")