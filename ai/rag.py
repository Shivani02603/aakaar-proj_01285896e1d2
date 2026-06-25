import os
from .embeddings import get_embedding
from pgvector.asyncpg import VectorStore
import openai

async def retrieve_context(query: str, top_k: int, session_id: str, user_id: str):
    embedding = await get_embedding(query)
    vector_store = VectorStore()
    await vector_store.connect(os.getenv('PGVECTOR_CONNECTION_STRING'))
    results = await vector_store.search(embedding, top_k)
    return results

async def answer_question(query: str, session_id: str, user_id: str) -> dict:
    # Retrieve context
    retrieved_chunks = await retrieve_context(query, top_k=5, session_id=session_id, user_id=user_id)
    if not retrieved_chunks:
        return {'answer': "No relevant information found.", 'sources': []}

    # Build prompt
    context = "\n".join([chunk['text'] for chunk in retrieved_chunks])
    prompt = f"Answer the following question based on the context provided:\n\nContext:\n{context}\n\nQuestion:\n{query}"

    # Call the runtime LLM
    openai_api_key = os.getenv('OPENAI_API_KEY')
    client = openai.OpenAI(api_key=openai_api_key)
    response = client.chat.completions.create(
        model='gpt-4o',
        messages=[{'role': 'user', 'content': prompt}]
    )
    answer = response.choices[0].message.content

    # Build sources
    sources = [{'filename': chunk['source_filename'], 'location': chunk['page_or_row']} for chunk in retrieved_chunks]

    return {'answer': answer, 'sources': sources}