import os
import tempfile
from fastapi import UploadFile
import tiktoken
from pypdf import PdfReader
from .embeddings import get_embedding
from pgvector.asyncpg import VectorStore

async def chunk(text: str, chunk_size: int = 1000, overlap: int = 200):
    enc = tiktoken.get_encoding('cl100k_base')
    tokens = enc.encode(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = enc.decode(chunk_tokens)
        chunks.append(chunk_text)
        start += chunk_size - overlap
    return chunks

async def ingest_pdf(file: UploadFile, session_id: str, user_id: str):
    # Save the uploaded file to a temporary location
    contents = await file.read()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename or '')[1])
    tmp.write(contents)
    tmp.flush()
    file_path = tmp.name

    try:
        # Extract text from the PDF
        reader = PdfReader(file_path)
        text_by_page = [page.extract_text() for page in reader.pages]
        original_filename = file.filename or "unknown"
        all_chunks = []
        chunk_index = 0

        for page_number, page_text in enumerate(text_by_page):
            chunks = await chunk(page_text)
            for chunk_text in chunks:
                metadata = {
                    'source_filename': original_filename,
                    'chunk_index': chunk_index,
                    'total_chunks': len(chunks),
                    'page_or_row': f"Page {page_number + 1}"
                }
                embedding = await get_embedding(chunk_text)
                all_chunks.append((embedding, metadata))
                chunk_index += 1

        # Store chunks in the vector store
        vector_store = VectorStore()
        await vector_store.connect(os.getenv('PGVECTOR_CONNECTION_STRING'))
        for embedding, metadata in all_chunks:
            await vector_store.insert(embedding, metadata)

    finally:
        # Clean up the temporary file
        os.unlink(file_path)