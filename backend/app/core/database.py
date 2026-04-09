from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Create synchronous engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG  # logs all SQL queries when DEBUG=True — very helpful
)

# Session factory — each request gets its own session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    """
    Dependency — gives each API route its own database session
    and closes it cleanly when the request is done.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Run once at startup — enables pgvector extension
    and creates all tables.
    """
    with engine.connect() as conn:
        # Enable pgvector — must be done before creating vector columns
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    # Create all tables defined in models
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully.")