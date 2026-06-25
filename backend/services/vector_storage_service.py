import uuid
from typing import List, Optional

from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from database.models import DocumentChunk
from database.config import get_db


class VectorStorageService:
    def create_chunk(self, chunk_data: dict, db: Session = Depends(get_db)) -> DocumentChunk:
        """
        Create a new document chunk and store it in the database.
        """
        try:
            new_chunk = DocumentChunk(
                id=uuid.uuid4(),
                document_id=chunk_data["document_id"],
                chunk_index=chunk_data["chunk_index"],
                content=chunk_data["content"],
                embedding=chunk_data["embedding"],
                metadata=chunk_data["metadata"],
            )
            db.add(new_chunk)
            db.commit()
            db.refresh(new_chunk)
            return new_chunk
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create chunk: {str(e)}")

    def get_chunk_by_id(self, chunk_id: uuid.UUID, db: Session = Depends(get_db)) -> DocumentChunk:
        """
        Retrieve a document chunk by its ID.
        """
        chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
        if not chunk:
            raise HTTPException(status_code=404, detail="Chunk not found")
        return chunk

    def list_all_chunks(self, db: Session = Depends(get_db)) -> List[DocumentChunk]:
        """
        List all document chunks in the database.
        """
        try:
            chunks = db.query(DocumentChunk).all()
            return chunks
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Failed to list chunks: {str(e)}")

    def update_chunk(self, chunk_id: uuid.UUID, chunk_update: dict, db: Session = Depends(get_db)) -> DocumentChunk:
        """
        Update an existing document chunk.
        """
        chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
        if not chunk:
            raise HTTPException(status_code=404, detail="Chunk not found")

        try:
            for key, value in chunk_update.items():
                setattr(chunk, key, value)
            db.commit()
            db.refresh(chunk)
            return chunk
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update chunk: {str(e)}")

    def delete_chunk(self, chunk_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
        """
        Delete a document chunk by its ID.
        """
        chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
        if not chunk:
            raise HTTPException(status_code=404, detail="Chunk not found")

        try:
            db.delete(chunk)
            db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete chunk: {str(e)}")