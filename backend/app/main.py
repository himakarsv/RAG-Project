# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware

# app = FastAPI(
#     title="Multimodal RAG API",
#     description="A scalable RAG pipeline supporting text, images, audio and more",
#     version="0.1.0"
# )

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000"],  # Next.js frontend URL
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# @app.get("/")
# def root():
#     return {"message": "Multimodal RAG API is running"}

# @app.get("/health")
# def health_check():
#     return {
#         "status": "healthy",
#         "version": "0.1.0"
#     }












# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from app.api.upload import router as upload_router

# app = FastAPI(
#     title="Multimodal RAG API",
#     description="A scalable RAG pipeline supporting text, images, audio and more",
#     version="0.1.0"
# )

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Register routers
# app.include_router(upload_router, prefix="/api/v1", tags=["Upload"])

# @app.get("/")
# def root():
#     return {"message": "Multimodal RAG API is running"}

# @app.get("/health")
# def health_check():
#     return {"status": "healthy", "version": "0.1.0"}














# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from app.api.upload import router as upload_router
# from app.core.database import init_db

# app = FastAPI(
#     title="Multimodal RAG API",
#     description="A scalable RAG pipeline supporting text, images, audio and more",
#     version="0.1.0"
# )

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# app.include_router(upload_router, prefix="/api/v1", tags=["Upload"])


# @app.on_event("startup")
# def on_startup():
#     """Runs once when the server starts — sets up DB tables."""
#     init_db()


# @app.get("/")
# def root():
#     return {"message": "Multimodal RAG API is running"}


# @app.get("/health")
# def health_check():
#     return {"status": "healthy", "version": "0.1.0"}










from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.upload import router as upload_router
from app.api.query import router as query_router
from app.core.database import init_db

app = FastAPI(
    title="Multimodal RAG API",
    description="A scalable RAG pipeline supporting text, images, audio and more",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router, prefix="/api/v1", tags=["Upload"])
app.include_router(query_router, prefix="/api/v1", tags=["Query"])


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def root():
    return {"message": "Multimodal RAG API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "0.1.0"}