# from pydantic_settings import BaseSettings
# from pathlib import Path

# class Settings(BaseSettings):
#     APP_NAME: str = "Multimodal RAG API"
#     DEBUG: bool = True
#     OPENAI_API_KEY: str = ""

#     # File upload settings
#     UPLOAD_DIR: Path = Path("uploads")
#     MAX_FILE_SIZE_MB: int = 50
#     ALLOWED_EXTENSIONS: list = [
#         ".pdf", ".docx", ".doc",
#         ".xlsx", ".xls", ".csv",
#         ".png", ".jpg", ".jpeg", ".webp",
#         ".mp3", ".mp4", ".wav",
#         ".txt", ".md"
#     ]

#     # System tool paths
#     POPPLER_PATH: str = r"E:\poppler-25.12.0\Library\bin"
#     TESSERACT_PATH: str = r"E:\Tesseract\tesseract.exe"

#     class Config:
#         env_file = ".env"

# settings = Settings()
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    APP_NAME: str = "Multimodal RAG API"
    DEBUG: bool = True
    OPENAI_API_KEY: str = ""

    # File upload
    UPLOAD_DIR: Path = Path("uploads")
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: list = [
        ".pdf", ".docx", ".doc",
        ".xlsx", ".xls", ".csv",
        ".png", ".jpg", ".jpeg", ".webp",
        ".mp3", ".mp4", ".wav",
        ".txt", ".md"
    ]

    # System tool paths
    POPPLER_PATH: str = r"E:\poppler-25.12.0\Library\bin"
    TESSERACT_PATH: str = r"E:\Tesseract\tesseract.exe"

    # Database
    DATABASE_URL: str = ""

    class Config:
        env_file = ".env"

settings = Settings()