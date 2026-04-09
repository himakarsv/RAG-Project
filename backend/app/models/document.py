from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.core.database import Base


class Document(Base):
    """
    Stores metadata about each uploaded file.
    One row per uploaded document.
    """
    __tablename__ = "documents"

    id = Column(String, primary_key=True)  # UUID
    filename = Column(String, nullable=False)
    saved_as = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    size_mb = Column(Float, nullable=False)
    total_chunks = Column(Integer, default=0)
    status = Column(String, default="processing")  # processing | ready | failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DocumentChunk(Base):
    """
    Stores each chunk of text and its embedding vector.
    One row per chunk — a document with 12 chunks = 12 rows here.

    The embedding column stores 1536 numbers (OpenAI ada-002 output size).
    pgvector uses these numbers to find similar chunks via cosine similarity.
    """
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String, nullable=False)  # links back to Document
    content = Column(Text, nullable=False)         # the actual text of the chunk
    embedding = Column(Vector(1536))               # 1536-dim vector from OpenAI
    chunk_type = Column(String, default="text")    # text | table | image
    chunk_index = Column(Integer, default=0)       # position within document
    doc_metadata = Column(JSON, default={})        # filename, page, heading etc
    created_at = Column(DateTime(timezone=True), server_default=func.now())