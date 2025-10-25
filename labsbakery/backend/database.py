"""
🧁 LabsBakery Core - Database Module
Handles database connection and session management
"""
from sqlmodel import SQLModel, create_engine, Session
from backend.config import get_settings

settings = get_settings()

# Create database engine
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)


def init_db():
    """Initialize database and create all tables"""
    SQLModel.metadata.create_all(engine)
    print("✅ Database initialized successfully")


def get_session():
    """Get database session (dependency injection)"""
    with Session(engine) as session:
        yield session


def drop_db():
    """Drop all tables (use with caution!)"""
    SQLModel.metadata.drop_all(engine)
    print("⚠️  Database dropped")
