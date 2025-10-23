"""
Database connection module for Twarga Cloud MVP
Handles SQLite database connection and session management
"""

import os
import logging
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./twarga_cloud.db")

# Create engine
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={
            "check_same_thread": False,
            "timeout": 20
        },
        poolclass=StaticPool,
        echo=os.getenv("DEBUG", "False").lower() == "true"
    )
else:
    engine = create_engine(
        DATABASE_URL,
        echo=os.getenv("DEBUG", "False").lower() == "true"
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()

def get_db() -> Session:
    """
    Dependency function to get database session
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    """
    Initialize database by running migrations and creating default data
    """
    try:
        logger.info("Initializing database...")
        
        # Run migrations (imported lazily to avoid circular import)
        from .migrations import run_migrations
        run_migrations()
        logger.info("Database migrations completed")
        
        # Create default admin user if not exists
        from .models import User
        db = SessionLocal()
        try:
            # Check if admin user exists
            admin_user = db.query(User).filter(User.username == "admin").first()
            if not admin_user:
                # Create default admin user
                from .auth import get_password_hash
                admin_user = User(
                    username="admin",
                    email="admin@twarga.cloud",
                    hashed_password=get_password_hash("admin123"),
                    is_active=True,
                    is_admin=True,
                    credits=1000
                )
                db.add(admin_user)
                db.commit()
                logger.info("Default admin user created")
            else:
                logger.info("Admin user already exists")
        except Exception as e:
            logger.error(f"Error creating default admin user: {e}")
            db.rollback()
        finally:
            db.close()
            
        logger.info("Database initialization completed successfully")
            
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

def get_db_session() -> Session:
    """
    Get a database session (for use outside of dependency injection)
    """
    return SessionLocal()

def close_db(db: Session):
    """
    Close database session
    """
    try:
        db.close()
    except Exception as e:
        logger.error(f"Error closing database session: {e}")

def check_db_connection() -> bool:
    """
    Check if database connection is working
    """
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

def get_database_info() -> dict:
    """
    Get database information
    """
    try:
        db = SessionLocal()
        
        # Get database file size for SQLite
        if DATABASE_URL.startswith("sqlite"):
            db_path = DATABASE_URL.replace("sqlite:///", "")
            if os.path.exists(db_path):
                size = os.path.getsize(db_path)
                size_mb = size / (1024 * 1024)
            else:
                size_mb = 0
        else:
            size_mb = 0
        
        # Get table counts
        from .models import User, VM, Event
        
        user_count = db.query(User).count()
        vm_count = db.query(VM).count()
        event_count = db.query(Event).count()
        
        db.close()
        
        return {
            "database_url": DATABASE_URL,
            "size_mb": round(size_mb, 2),
            "tables": {
                "users": user_count,
                "vms": vm_count,
                "events": event_count
            },
            "connection_status": "connected"
        }
    except Exception as e:
        logger.error(f"Error getting database info: {e}")
        return {
            "database_url": DATABASE_URL,
            "size_mb": 0,
            "tables": {"users": 0, "vms": 0, "events": 0},
            "connection_status": "disconnected",
            "error": str(e)
        }

def reset_database():
    """
    Reset database by dropping all tables and recreating them
    WARNING: This will delete all data!
    """
    try:
        logger.warning("Resetting database - all data will be deleted!")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        
        # Recreate default admin user
        init_db()
        
        logger.info("Database reset successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to reset database: {e}")
        return False

# Database health check function
def health_check() -> dict:
    """
    Perform database health check
    """
    try:
        db = SessionLocal()
        start_time = time.time()
        db.execute(text("SELECT 1"))
        response_time = time.time() - start_time
        db.close()
        
        return {
            "status": "healthy",
            "response_time_ms": round(response_time * 1000, 2),
            "database_url": DATABASE_URL
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "database_url": DATABASE_URL
        }

# Import time for health check
import time