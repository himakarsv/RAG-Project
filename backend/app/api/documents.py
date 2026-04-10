from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.document import Document, DocumentChunk

router = APIRouter()


@router.get("/documents")
def list_documents(db: Session = Depends(get_db)):
    """
    Returns all uploaded documents.
    The frontend uses this to show the document library.
    """
    documents = db.query(Document).order_by(Document.created_at.desc()).all()

    return [
        {
            "document_id": doc.id,
            "filename": doc.filename,
            "file_type": doc.file_type,
            "size_mb": doc.size_mb,
            "total_chunks": doc.total_chunks,
            "status": doc.status,
            "created_at": doc.created_at
        }
        for doc in documents
    ]


@router.get("/documents/{document_id}")
def get_document(document_id: str, db: Session = Depends(get_db)):
    """
    Returns details of a single document including its chunks.
    Useful for the frontend to show document preview.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    chunks = db.query(DocumentChunk).filter(
        DocumentChunk.document_id == document_id
    ).order_by(DocumentChunk.chunk_index).all()

    return {
        "document_id": doc.id,
        "filename": doc.filename,
        "file_type": doc.file_type,
        "size_mb": doc.size_mb,
        "total_chunks": doc.total_chunks,
        "status": doc.status,
        "created_at": doc.created_at,
        "chunks": [
            {
                "chunk_index": chunk.chunk_index,
                "chunk_type": chunk.chunk_type,
                "content": chunk.content[:300] + "..." if len(chunk.content) > 300 else chunk.content,
                "metadata": chunk.doc_metadata
            }
            for chunk in chunks
        ]
    }


@router.delete("/documents/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db)):
    """
    Deletes a document and all its chunks from the database.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    # Delete all chunks first (foreign key order)
    db.query(DocumentChunk).filter(
        DocumentChunk.document_id == document_id
    ).delete()

    # Then delete the document record
    db.delete(doc)
    db.commit()

    return {"message": f"Document '{doc.filename}' deleted successfully."}