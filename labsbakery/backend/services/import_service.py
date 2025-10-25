"""
🧁 LabsBakery Core - Import Service
Handles importing lab projects from .labpkg files
"""
import json
import os
import shutil
import zipfile
import uuid
from pathlib import Path
from typing import Tuple, Dict

from sqlmodel import Session

from backend.models import Project, VM, ProjectCreate
from backend.utils.schema_validator import validate_lab


class ImportService:
    """Service for importing lab projects from .labpkg ZIP files"""
    
    def __init__(self, base_dir: str = "/tmp/labsbakery-imports"):
        """
        Initialize import service
        
        Args:
            base_dir: Base directory for temporary import files
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def import_lab(
        self,
        labpkg_path: str,
        session: Session,
        assets_base_dir: str = "data/projects"
    ) -> Tuple[int, Dict]:
        """
        Import a lab from .labpkg file
        
        Args:
            labpkg_path: Path to .labpkg file
            session: Database session
            assets_base_dir: Base directory for storing assets
            
        Returns:
            Tuple of (project_id, import_info)
        """
        # Create temporary extraction directory
        extract_id = f"import-{uuid.uuid4().hex[:8]}"
        extract_dir = self.base_dir / extract_id
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Extract ZIP file
            self._extract_zip(labpkg_path, extract_dir)
            
            # Validate structure
            self._validate_structure(extract_dir)
            
            # Load lab.json
            lab_json_path = extract_dir / "lab.json"
            with open(lab_json_path, "r") as f:
                lab_data = json.load(f)
            
            # Validate lab data
            validation = validate_lab(lab_data)
            if not validation["valid"]:
                raise ValueError(f"Lab validation failed: {validation['errors']}")
            
            # Create project in database
            project = self._create_project(lab_data, session)
            
            # Create VMs in database
            vms_created = self._create_vms(lab_data, project.id, session)
            
            # Copy assets if they exist
            assets_src = extract_dir / "assets"
            if assets_src.exists():
                assets_dest = Path(assets_base_dir) / str(project.id) / "assets"
                assets_dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(assets_src, assets_dest)
            
            # Build import info
            import_info = {
                "project_id": project.id,
                "title": project.title,
                "author": project.author,
                "vms_created": vms_created,
                "validation_warnings": validation.get("warnings", []),
                "status": "success"
            }
            
            return project.id, import_info
            
        except Exception as e:
            # Rollback on error
            session.rollback()
            raise Exception(f"Import failed: {str(e)}")
            
        finally:
            # Clean up temporary directory
            if extract_dir.exists():
                shutil.rmtree(extract_dir)
    
    def _extract_zip(self, zip_path: str, extract_dir: Path):
        """
        Extract ZIP file to directory
        
        Args:
            zip_path: Path to ZIP file
            extract_dir: Destination directory
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                zipf.extractall(extract_dir)
        except zipfile.BadZipFile:
            raise ValueError("Invalid .labpkg file: not a valid ZIP")
    
    def _validate_structure(self, extract_dir: Path):
        """
        Validate extracted .labpkg structure
        
        Args:
            extract_dir: Extracted directory path
        """
        # Check for required files
        lab_json = extract_dir / "lab.json"
        if not lab_json.exists():
            raise ValueError("Invalid .labpkg: missing lab.json")
        
        # metadata.json is optional but recommended
        metadata_json = extract_dir / "metadata.json"
        if not metadata_json.exists():
            print("⚠️  Warning: metadata.json not found (optional)")
    
    def _create_project(self, lab_data: Dict, session: Session) -> Project:
        """
        Create project from lab data
        
        Args:
            lab_data: Lab data dictionary
            session: Database session
            
        Returns:
            Created Project instance
        """
        metadata = lab_data["metadata"]
        
        # Create project
        project = Project(
            title=metadata["title"],
            description=metadata.get("description", ""),
            author=metadata["author"],
            schema_version=lab_data["schemaVersion"],
            canvas_state=json.dumps(lab_data.get("canvas", {})),
            tutorial_content=json.dumps(lab_data.get("tutorial", {})),
            status="draft",
            tags=",".join(metadata.get("tags", []))
        )
        
        session.add(project)
        session.commit()
        session.refresh(project)
        
        return project
    
    def _create_vms(self, lab_data: Dict, project_id: int, session: Session) -> int:
        """
        Create VMs from lab data
        
        Args:
            lab_data: Lab data dictionary
            project_id: Project ID
            session: Database session
            
        Returns:
            Number of VMs created
        """
        ingredients = lab_data.get("ingredients", [])
        
        for ingredient in ingredients:
            vm = VM(
                project_id=project_id,
                name=ingredient["name"],
                box=ingredient["box"],
                ram_mb=ingredient.get("ram", 2048),
                cpu_cores=ingredient.get("cpu", 2),
                network_id=ingredient.get("network", "default"),
                ip_address=ingredient.get("ip", "192.168.56.10"),
                status="pending"
            )
            session.add(vm)
        
        session.commit()
        
        return len(ingredients)
    
    def validate_labpkg(self, labpkg_path: str) -> Dict:
        """
        Validate a .labpkg file without importing
        
        Args:
            labpkg_path: Path to .labpkg file
            
        Returns:
            Validation results dictionary
        """
        extract_id = f"validate-{uuid.uuid4().hex[:8]}"
        extract_dir = self.base_dir / extract_id
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Extract and validate
            self._extract_zip(labpkg_path, extract_dir)
            self._validate_structure(extract_dir)
            
            # Load and validate lab.json
            lab_json_path = extract_dir / "lab.json"
            with open(lab_json_path, "r") as f:
                lab_data = json.load(f)
            
            validation = validate_lab(lab_data)
            
            # Add file size info
            file_size = os.path.getsize(labpkg_path)
            validation["file_size_mb"] = round(file_size / (1024 * 1024), 2)
            
            # Add VM count
            validation["vm_count"] = len(lab_data.get("ingredients", []))
            
            return validation
            
        except Exception as e:
            return {
                "valid": False,
                "errors": [str(e)],
                "warnings": []
            }
            
        finally:
            # Clean up
            if extract_dir.exists():
                shutil.rmtree(extract_dir)
