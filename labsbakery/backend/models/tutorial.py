"""
🧁 LabsBakery Core - Tutorial Model
Defines database schemas for tutorials and steps
"""
from typing import Optional
from sqlmodel import SQLModel, Field


class TutorialStep(SQLModel, table=True):
    """
    Tutorial Step Model
    Represents a single step in a lab tutorial
    """
    
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id", index=True)
    
    # Step Configuration
    step_number: int = Field(ge=1)  # 1, 2, 3, etc.
    title: str = Field(max_length=255)
    content: str = Field()  # Rich text content (HTML or Markdown)
    
    # Optional VM linking
    linked_vm_id: Optional[int] = Field(default=None, foreign_key="vm.id")
    
    # Step requirements
    is_required: bool = Field(default=True)
    estimated_minutes: Optional[int] = Field(default=None, ge=1)
    
    # Hints and tips
    hint: Optional[str] = Field(default=None, max_length=1000)
    expected_output: Optional[str] = Field(default=None, max_length=2000)
    
    class Config:
        json_schema_extra = {
            "example": {
                "project_id": 1,
                "step_number": 1,
                "title": "Setup Environment",
                "content": "<h2>Step 1: Setup</h2><p>Update Kali Linux...</p>",
                "is_required": True,
                "estimated_minutes": 5
            }
        }


class StudentProgress(SQLModel, table=True):
    """
    Student Progress Model
    Tracks student progress through tutorial steps
    """
    
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id", index=True)
    student_id: str = Field(max_length=100, index=True)  # User ID or session ID
    
    # Progress tracking
    completed_steps: str = Field(default="")  # Comma-separated step IDs
    current_step: int = Field(default=1)
    progress_percentage: int = Field(default=0, ge=0, le=100)
    
    # Timestamps
    started_at: Optional[str] = None
    last_activity: Optional[str] = None
    completed_at: Optional[str] = None
    
    # Notes
    notes: Optional[str] = Field(default=None, max_length=5000)
    
    class Config:
        json_schema_extra = {
            "example": {
                "project_id": 1,
                "student_id": "student123",
                "completed_steps": "1,2,3",
                "current_step": 4,
                "progress_percentage": 60
            }
        }


class TutorialStepCreate(SQLModel):
    """Schema for creating a tutorial step"""
    project_id: int
    step_number: int
    title: str
    content: str
    linked_vm_id: Optional[int] = None
    is_required: bool = True
    estimated_minutes: Optional[int] = None
    hint: Optional[str] = None
    expected_output: Optional[str] = None


class TutorialStepUpdate(SQLModel):
    """Schema for updating a tutorial step"""
    title: Optional[str] = None
    content: Optional[str] = None
    linked_vm_id: Optional[int] = None
    is_required: Optional[bool] = None
    estimated_minutes: Optional[int] = None
    hint: Optional[str] = None
    expected_output: Optional[str] = None
