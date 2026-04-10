from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.services.retriever import retrieve_similar_chunks
from app.services.llm import generate_answer

router = APIRouter()


class QueryRequest(BaseModel):
    question: str
    document_id: Optional[str] = None  # if None, searches all documents
    top_k: int = 5                      # how many chunks to retrieve


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: list
    model: str
    chunks_used: int


@router.post("/query", response_model=QueryResponse)
def query_documents(
    request: QueryRequest,
    db: Session = Depends(get_db)
):
    """
    Ask a question against your uploaded documents.

    Steps:
    1. Embed the question
    2. Find the most similar chunks in pgvector
    3. Send those chunks + question to GPT
    4. Return the answer with sources
    """

    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    if request.top_k < 1 or request.top_k > 20:
        raise HTTPException(status_code=400, detail="top_k must be between 1 and 20.")

    # Retrieve relevant chunks
    chunks = retrieve_similar_chunks(
        query=request.question,
        db=db,
        document_id=request.document_id,
        top_k=request.top_k
    )

    # Generate answer using retrieved chunks
    result = generate_answer(
        query=request.question,
        chunks=chunks
    )

    return QueryResponse(
        question=request.question,
        answer=result["answer"],
        sources=result["sources"],
        model=result["model"],
        chunks_used=result["chunks_used"]
    )