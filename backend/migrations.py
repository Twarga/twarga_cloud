"""
Database migration scripts for Twarga Cloud MVP
Handles database schema evolution and versioning
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy import text, inspect
from .database import engine, Base
from .models import User, VM, Event, Metric

logger = logging.getLogger(__name__)

class MigrationManager:
    """
    Manages database migrations and schema updates
    """
    
    def __init__(self):
        self.migrations = [
            {
                "version": "001",
                "name": "initial_schema",
                "description": "Create initial database schema",
                "up": self._create_initial_schema,
                "down": self._drop_initial_schema
            },
            {
                "version": "002",
                "name": "add_metrics_table",
                "description": "Add metrics table for monitoring data",
                "up": self._add_metrics_table,
                "down": self._remove_metrics_table
            }
        ]
        
        # Migration history table name
        self.migration_table = "migration_history"
    
    def _ensure_migration_table(self):
        """
        Create migration history table if it doesn't exist
        """
        with engine.connect() as conn:
            inspector = inspect(engine)
            if self.migration_table not in inspector.get_table_names():
                conn.execute(text(f"""
                    CREATE TABLE {self.migration_table} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        version VARCHAR(10) NOT NULL UNIQUE,
                        name VARCHAR(100) NOT NULL,
                        description TEXT,
                        applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                conn.commit()
                logger.info(f"Created migration table: {self.migration_table}")
    
    def _get_applied_migrations(self) -> List[str]:
        """
        Get list of applied migrations from database
        """
        with engine.connect() as conn:
            try:
                result = conn.execute(text(f"SELECT version FROM {self.migration_table} ORDER BY version"))
                return [row[0] for row in result]
            except Exception as e:
                logger.error(f"Error getting applied migrations: {e}")
                return []
    
    def _record_migration(self, version: str, name: str, description: str):
        """
        Record migration as applied in migration history
        """
        with engine.connect() as conn:
            conn.execute(text(f"""
                INSERT INTO {self.migration_table} (version, name, description)
                VALUES (:version, :name, :description)
            """), {"version": version, "name": name, "description": description})
            conn.commit()
            logger.info(f"Recorded migration: {version} - {name}")
    
    def _remove_migration_record(self, version: str):
        """
        Remove migration record from migration history
        """
        with engine.connect() as conn:
            conn.execute(text(f"DELETE FROM {self.migration_table} WHERE version = :version"), 
                        {"version": version})
            conn.commit()
            logger.info(f"Removed migration record: {version}")
    
    def _create_initial_schema(self):
        """
        Create initial database schema
        """
        logger.info("Creating initial database schema...")
        Base.metadata.create_all(bind=engine)
        logger.info("Initial schema created successfully")
    
    def _drop_initial_schema(self):
        """
        Drop initial database schema
        """
        logger.warning("Dropping initial database schema...")
        Base.metadata.drop_all(bind=engine)
        logger.warning("Initial schema dropped")
    
    def _add_metrics_table(self):
        """
        Add metrics table for monitoring data
        """
        logger.info("Adding metrics table...")
        # Metrics table is already included in Base metadata
        # This is a placeholder for future migrations
        logger.info("Metrics table added successfully")
    
    def _remove_metrics_table(self):
        """
        Remove metrics table
        """
        logger.warning("Removing metrics table...")
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS metrics"))
            conn.commit()
        logger.warning("Metrics table removed")
    
    def migrate(self, target_version: Optional[str] = None):
        """
        Run migrations up to target version
        """
        logger.info("Starting database migration...")
        
        # Ensure migration table exists
        self._ensure_migration_table()
        
        # Get applied migrations
        applied_migrations = self._get_applied_migrations()
        
        # Determine migrations to run
        migrations_to_run = []
        for migration in self.migrations:
            if migration["version"] not in applied_migrations:
                if target_version is None or migration["version"] <= target_version:
                    migrations_to_run.append(migration)
        
        # Run migrations
        for migration in migrations_to_run:
            logger.info(f"Running migration: {migration['version']} - {migration['name']}")
            try:
                migration["up"]()
                self._record_migration(migration["version"], migration["name"], migration["description"])
                logger.info(f"Migration {migration['version']} completed successfully")
            except Exception as e:
                logger.error(f"Migration {migration['version']} failed: {e}")
                raise
        
        logger.info("Database migration completed successfully")
    
    def rollback(self, target_version: str):
        """
        Rollback migrations to target version
        """
        logger.warning(f"Rolling back to version: {target_version}")
        
        # Get applied migrations
        applied_migrations = self._get_applied_migrations()
        
        # Determine migrations to rollback
        migrations_to_rollback = []
        for migration in reversed(self.migrations):
            if migration["version"] in applied_migrations:
                if migration["version"] > target_version:
                    migrations_to_rollback.append(migration)
        
        # Run rollback migrations
        for migration in migrations_to_rollback:
            logger.warning(f"Rolling back migration: {migration['version']} - {migration['name']}")
            try:
                migration["down"]()
                self._remove_migration_record(migration["version"])
                logger.warning(f"Migration {migration['version']} rolled back successfully")
            except Exception as e:
                logger.error(f"Rollback of migration {migration['version']} failed: {e}")
                raise
        
        logger.warning(f"Rollback to version {target_version} completed")
    
    def get_migration_status(self) -> Dict:
        """
        Get current migration status
        """
        self._ensure_migration_table()
        applied_migrations = self._get_applied_migrations()
        
        available_versions = [m["version"] for m in self.migrations]
        pending_migrations = [v for v in available_versions if v not in applied_migrations]
        
        return {
            "available_migrations": len(self.migrations),
            "applied_migrations": len(applied_migrations),
            "pending_migrations": len(pending_migrations),
            "current_version": applied_migrations[-1] if applied_migrations else None,
            "latest_version": self.migrations[-1]["version"] if self.migrations else None,
            "applied_migration_list": applied_migrations,
            "pending_migration_list": pending_migrations
        }

# Global migration manager instance
migration_manager = MigrationManager()

def run_migrations(target_version: Optional[str] = None):
    """
    Run database migrations
    """
    migration_manager.migrate(target_version)

def rollback_migrations(target_version: str):
    """
    Rollback database migrations
    """
    migration_manager.rollback(target_version)

def get_migration_status():
    """
    Get migration status
    """
    return migration_manager.get_migration_status()