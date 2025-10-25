"""
🧁 LabsBakery Core - Project Model
Defines the database schema for lab projects
"""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Project(SQLModel, table=True):
    """
    Lab Project Model
    Represents a complete lab environment with VMs, networks, and tutorials
    """
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Metadata
    title: str = Field(index=True, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    author: str = Field(index=True, max_length=100)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Schema version for compatibility
    schema_version: int = Field(default=1)
    
    # JSON data (stored as strings)
    canvas_state: str = Field(default="{}")  # Canvas nodes and links
    tutorial_content: str = Field(default="{}")  # Tutorial steps
    
    # Status: draft, ready, running, stopped, error
    status: str = Field(default="draft", max_length=20)
    
    # Tags (comma-separated)
    tags: Optional[str] = Field(default=None, max_length=500)
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Web Pentesting 101",
                "description": "Learn SQL injection basics",
                "author": "Prof. Ahmed",
                "status": "draft",
                "tags": "web,pentest,beginner"
            }
        }


class ProjectCreate(SQLModel):
    """Schema for creating a new project"""
    title: str
    description: Optional[str] = None
    author: str
    tags: Optional[str] = None


class ProjectUpdate(SQLModel):
    """Schema for updating a project"""
    title: Optional[str] = None
    description: Optional[str] = None
    canvas_state: Optional[str] = None
    tutorial_content: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[str] = None


class ProjectRead(SQLModel):
    """Schema for reading a project (response model)"""
    id: int
    title: str
    description: Optional[str]
    author: str
    created_at: datetime
    updated_at: datetime
    schema_version: int
    canvas_state: str
    tutorial_content: str
    status: str
    tags: Optional[str]
