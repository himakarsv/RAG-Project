from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.document import DocumentChunk
from app.services.embedder import get_embedding
from typing import List, Dict, Any


def retrieve_similar_chunks(
    query: str,
    db: Session,
    document_id: str = None,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Find the most relevant chunks for a given query using
    cosine similarity search in pgvector.

    Steps:
    1. Embed the query into a vector
    2. Compare that vector against all stored chunk vectors
    3. Return the top_k most similar chunks

    The <=> operator is pgvector's cosine distance operator.
    Cosine distance 0 = identical, 1 = completely different.
    So we ORDER BY ASC to get the most similar first.
    """

    # Embed the user's question
    query_embedding = get_embedding(query)

    # Convert to string format pgvector expects
    embedding_str = str(query_embedding)

    # Build the similarity search query
    if document_id:
        # Search only within a specific document
        sql = text("""
            SELECT
                id,
                document_id,
                content,
                chunk_type,
                chunk_index,
                doc_metadata,
                1 - (embedding <=> CAST(:embedding AS vector)) AS similarity
            FROM document_chunks
            WHERE document_id = :document_id
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT :top_k
        """)
        results = db.execute(sql, {
            "embedding": embedding_str,
            "document_id": document_id,
            "top_k": top_k
        }).fetchall()
    else:
        # Search across ALL documents
        sql = text("""
            SELECT
                id,
                document_id,
                content,
                chunk_type,
                chunk_index,
                doc_metadata,
                1 - (embedding <=> CAST(:embedding AS vector)) AS similarity
            FROM document_chunks
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT :top_k
        """)
        results = db.execute(sql, {
            "embedding": embedding_str,
            "top_k": top_k
        }).fetchall()

    # Format results into clean dicts
    return [
        {
            "id": row.id,
            "document_id": row.document_id,
            "content": row.content,
            "chunk_type": row.chunk_type,
            "chunk_index": row.chunk_index,
            "metadata": row.doc_metadata,
            "similarity": round(float(row.similarity), 4)
        }
        for row in results
    ]