"""
🧁 LabsBakery Core - Projects API Routes
CRUD operations for lab projects
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlmodel import Session, select
from datetime import datetime

from backend.database import get_session
from backend.models import (
    Project,
    ProjectCreate,
    ProjectUpdate,
    ProjectRead,
    VM
)
from backend.services.export_service import ExportService
from backend.services.import_service import ImportService

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("/", response_model=List[ProjectRead])
def list_projects(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session)
):
    """
    List all lab projects
    
    Parameters:
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return
    """
    statement = select(Project).offset(skip).limit(limit)
    projects = session.exec(statement).all()
    return projects


@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    project: ProjectCreate,
    session: Session = Depends(get_session)
):
    """
    Create a new lab project
    
    Parameters:
    - project: Project creation data
    """
    # Create new project
    db_project = Project(
        title=project.title,
        description=project.description,
        author=project.author,
        tags=project.tags,
        canvas_state="{}",
        tutorial_content="{}",
        status="draft"
    )
    
    session.add(db_project)
    session.commit()
    session.refresh(db_project)
    
    return db_project


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(
    project_id: int,
    session: Session = Depends(get_session)
):
    """
    Get a specific lab project by ID
    
    Parameters:
    - project_id: Project ID
    """
    project = session.get(Project, project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found"
        )
    
    return project


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    session: Session = Depends(get_session)
):
    """
    Update a lab project
    
    Parameters:
    - project_id: Project ID
    - project_update: Fields to update
    """
    db_project = session.get(Project, project_id)
    
    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found"
        )
    
    # Update fields
    update_data = project_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_project, key, value)
    
    # Update timestamp
    db_project.updated_at = datetime.utcnow()
    
    session.add(db_project)
    session.commit()
    session.refresh(db_project)
    
    return db_project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    session: Session = Depends(get_session)
):
    """
    Delete a lab project
    
    Parameters:
    - project_id: Project ID
    """
    project = session.get(Project, project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found"
        )
    
    session.delete(project)
    session.commit()
    
    return None


@router.get("/{project_id}/stats")
def get_project_stats(
    project_id: int,
    session: Session = Depends(get_session)
):
    """
    Get statistics for a project (VM count, tutorial steps, etc.)
    
    Parameters:
    - project_id: Project ID
    """
    project = session.get(Project, project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found"
        )
    
    # TODO: Get VM count, tutorial step count, etc.
    # For now, return basic stats
    return {
        "project_id": project_id,
        "title": project.title,
        "status": project.status,
        "vm_count": 0,  # Will be implemented later
        "tutorial_steps": 0,  # Will be implemented later
        "created_at": project.created_at,
        "updated_at": project.updated_at
    }


@router.post("/{project_id}/export")
def export_project(
    project_id: int,
    session: Session = Depends(get_session)
):
    """
    Export a project as .labpkg file
    
    Parameters:
    - project_id: Project ID
    
    Returns:
    - File download response with .labpkg file
    """
    # Get project
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found"
        )
    
    # Get VMs for this project
    statement = select(VM).where(VM.project_id == project_id)
    vms = list(session.exec(statement).all())
    
    # Export lab
    try:
        export_service = ExportService()
        labpkg_path = export_service.export_lab(project, vms)
        
        return FileResponse(
            labpkg_path,
            media_type='application/zip',
            filename=f"{project.title.replace(' ', '_')}.labpkg"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )


@router.post("/import")
def import_project(
    file: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    """
    Import a project from .labpkg file
    
    Parameters:
    - file: Uploaded .labpkg file
    
    Returns:
    - Import results with project_id
    """
    # Validate file type
    if not file.filename.endswith('.labpkg'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a .labpkg file"
        )
    
    # Save uploaded file temporarily
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.labpkg') as temp_file:
        temp_file.write(file.file.read())
        temp_path = temp_file.name
    
    try:
        # Import lab
        import_service = ImportService()
        project_id, import_info = import_service.import_lab(temp_path, session)
        
        return {
            "status": "success",
            "project_id": project_id,
            "info": import_info
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.post("/validate")
def validate_labpkg(
    file: UploadFile = File(...),
):
    """
    Validate a .labpkg file without importing
    
    Parameters:
    - file: Uploaded .labpkg file
    
    Returns:
    - Validation results
    """
    # Validate file type
    if not file.filename.endswith('.labpkg'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a .labpkg file"
        )
    
    # Save uploaded file temporarily
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.labpkg') as temp_file:
        temp_file.write(file.file.read())
        temp_path = temp_file.name
    
    try:
        # Validate lab
        import_service = ImportService()
        validation = import_service.validate_labpkg(temp_path)
        
        return validation
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
