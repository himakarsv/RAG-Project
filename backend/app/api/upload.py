# import uuid
# import aiofiles
# from pathlib import Path
# from fastapi import APIRouter, UploadFile, File, HTTPException
# from app.core.config import settings
# from app.services.parser import extract_text_from_file

# router = APIRouter()


# @router.post("/upload")
# async def upload_file(file: UploadFile = File(...)):
#     """
#     Upload a file and extract its text content.
#     """

#     # 1. Check file extension is allowed
#     file_extension = Path(file.filename).suffix.lower()
#     if file_extension not in settings.ALLOWED_EXTENSIONS:
#         raise HTTPException(
#             status_code=400,
#             detail=f"File type '{file_extension}' is not supported. Allowed: {settings.ALLOWED_EXTENSIONS}"
#         )

#     # 2. Check file size (read into memory temporarily)
#     contents = await file.read()
#     size_mb = len(contents) / (1024 * 1024)
#     if size_mb > settings.MAX_FILE_SIZE_MB:
#         raise HTTPException(
#             status_code=400,
#             detail=f"File size {size_mb:.1f}MB exceeds the {settings.MAX_FILE_SIZE_MB}MB limit"
#         )

#     # 3. Generate a unique filename so nothing gets overwritten
#     unique_filename = f"{uuid.uuid4()}{file_extension}"
#     file_path = settings.UPLOAD_DIR / unique_filename

#     # 4. Save file to disk
#     async with aiofiles.open(file_path, "wb") as f:
#         await f.write(contents)

#     # 5. Parse the file
#     extracted = extract_text_from_file(file_path, file_extension)

#     # 6. Return results
#     return {
#         "filename": file.filename,
#         "saved_as": unique_filename,
#         "file_type": file_extension,
#         "size_mb": round(size_mb, 2),
#         "extraction": extracted
#     }











# import uuid
# import aiofiles
# from pathlib import Path
# from fastapi import APIRouter, UploadFile, File, HTTPException
# from app.core.config import settings
# from app.services.parser import extract_text_from_file
# from app.services.chunker import chunk_document

# router = APIRouter()


# @router.post("/upload")
# async def upload_file(file: UploadFile = File(...)):

#     # 1. Validate file extension
#     file_extension = Path(file.filename).suffix.lower()
#     if file_extension not in settings.ALLOWED_EXTENSIONS:
#         raise HTTPException(
#             status_code=400,
#             detail=f"File type '{file_extension}' is not supported."
#         )

#     # 2. Validate file size
#     contents = await file.read()
#     size_mb = len(contents) / (1024 * 1024)
#     if size_mb > settings.MAX_FILE_SIZE_MB:
#         raise HTTPException(
#             status_code=400,
#             detail=f"File too large. Max size is {settings.MAX_FILE_SIZE_MB}MB."
#         )

#     # 3. Save file with unique name
#     unique_filename = f"{uuid.uuid4()}{file_extension}"
#     file_path = settings.UPLOAD_DIR / unique_filename
#     async with aiofiles.open(file_path, "wb") as f:
#         await f.write(contents)

#     # 4. Parse the file
#     extracted = extract_text_from_file(file_path, file_extension)

#     # 5. Chunk the extracted content
#     document_metadata = {
#         "filename": file.filename,
#         "saved_as": unique_filename,
#         "file_type": file_extension,
#         "size_mb": round(size_mb, 2)
#     }
#     chunks = chunk_document(extracted, document_metadata)

#     # 6. Return everything
#     return {
#         "filename": file.filename,
#         "saved_as": unique_filename,
#         "file_type": file_extension,
#         "size_mb": round(size_mb, 2),
#         "total_chunks": len(chunks),
#         "chunks": chunks
#     }










import uuid
import aiofiles
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.document import Document, DocumentChunk
from app.services.parser import extract_text_from_file
from app.services.chunker import chunk_document
from app.services.embedder import get_embeddings_batch

router = APIRouter()


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)  # database session injected automatically
):
    # 1. Validate extension
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type '{file_extension}' not supported.")

    # 2. Validate size
    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > settings.MAX_FILE_SIZE_MB:
        raise HTTPException(status_code=400, detail=f"File too large. Max {settings.MAX_FILE_SIZE_MB}MB.")

    # 3. Save file
    document_id = str(uuid.uuid4())
    unique_filename = f"{document_id}{file_extension}"
    file_path = settings.UPLOAD_DIR / unique_filename
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(contents)

    # 4. Save document record to DB with status "processing"
    document = Document(
        id=document_id,
        filename=file.filename,
        saved_as=unique_filename,
        file_type=file_extension,
        size_mb=round(size_mb, 2),
        status="processing"
    )
    db.add(document)
    db.commit()

    # 5. Parse
    extracted = extract_text_from_file(file_path, file_extension)

    # 6. Chunk
    document_metadata = {
        "document_id": document_id,
        "filename": file.filename,
        "saved_as": unique_filename,
        "file_type": file_extension,
        "size_mb": round(size_mb, 2)
    }
    chunks = chunk_document(extracted, document_metadata)

    # 7. Embed all chunks in one batch call
    chunk_texts = [chunk["content"] for chunk in chunks]
    embeddings = get_embeddings_batch(chunk_texts)

    # 8. Save all chunks + embeddings to DB
    for chunk, embedding in zip(chunks, embeddings):
        db_chunk = DocumentChunk(
            document_id=document_id,
            content=chunk["content"],
            embedding=embedding,
            chunk_type=chunk["chunk_type"],
            chunk_index=chunk["document_chunk_index"],
            doc_metadata=chunk["metadata"]
        )
        db.add(db_chunk)

    # 9. Update document status to "ready"
    document.total_chunks = len(chunks)
    document.status = "ready"
    db.commit()

    return {
        "document_id": document_id,
        "filename": file.filename,
        "file_type": file_extension,
        "size_mb": round(size_mb, 2),
        "total_chunks": len(chunks),
        "status": "ready",
        "message": f"Document processed and {len(chunks)} chunks embedded successfully."
    }