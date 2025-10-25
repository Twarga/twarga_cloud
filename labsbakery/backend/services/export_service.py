"""
🧁 LabsBakery Core - Export Service
Handles exporting lab projects as .labpkg files
"""
import json
import os
import shutil
import zipfile
from pathlib import Path
from typing import Optional
from datetime import datetime

from backend.models import Project, VM
from backend.utils.schema_validator import validate_lab


class ExportService:
    """Service for exporting lab projects as .labpkg ZIP files"""
    
    def __init__(self, base_dir: str = "/tmp/labsbakery-exports"):
        """
        Initialize export service
        
        Args:
            base_dir: Base directory for temporary export files
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def export_lab(
        self,
        project: Project,
        vms: list[VM],
        assets_dir: Optional[str] = None
    ) -> str:
        """
        Export a lab project as .labpkg file
        
        Args:
            project: Project model instance
            vms: List of VM model instances
            assets_dir: Optional path to assets directory
            
        Returns:
            Path to created .labpkg file
        """
        # Create temporary export directory
        export_id = f"export-{project.id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        temp_dir = self.base_dir / export_id
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Build lab.json
            lab_data = self._build_lab_data(project, vms)
            
            # Validate before export
            validation = validate_lab(lab_data)
            if not validation["valid"]:
                raise ValueError(f"Lab validation failed: {validation['errors']}")
            
            # Write lab.json
            lab_json_path = temp_dir / "lab.json"
            with open(lab_json_path, "w") as f:
                json.dump(lab_data, f, indent=2)
            
            # Write metadata.json
            metadata = {
                "title": project.title,
                "author": project.author,
                "description": project.description,
                "version": project.schema_version,
                "created": project.created_at.isoformat(),
                "exported": datetime.utcnow().isoformat()
            }
            metadata_path = temp_dir / "metadata.json"
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)
            
            # Copy assets if they exist
            if assets_dir and os.path.exists(assets_dir):
                assets_dest = temp_dir / "assets"
                shutil.copytree(assets_dir, assets_dest)
            
            # Create ZIP file
            zip_filename = f"{self._sanitize_filename(project.title)}.labpkg"
            zip_path = self.base_dir / zip_filename
            
            self._create_zip(temp_dir, zip_path)
            
            return str(zip_path)
            
        finally:
            # Clean up temporary directory
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
    
    def _build_lab_data(self, project: Project, vms: list[VM]) -> dict:
        """
        Build lab.json data structure
        
        Args:
            project: Project model instance
            vms: List of VM model instances
            
        Returns:
            Lab data dictionary
        """
        # Parse canvas state
        try:
            canvas = json.loads(project.canvas_state)
        except json.JSONDecodeError:
            canvas = {"nodes": [], "links": []}
        
        # Parse tutorial content
        try:
            tutorial = json.loads(project.tutorial_content)
        except json.JSONDecodeError:
            tutorial = {"steps": []}
        
        # Build ingredients from VMs
        ingredients = [
            {
                "id": str(vm.id),
                "name": vm.name,
                "box": vm.box,
                "ram": vm.ram_mb,
                "cpu": vm.cpu_cores,
                "network": vm.network_id,
                "ip": vm.ip_address
            }
            for vm in vms
        ]
        
        # Build complete lab data
        lab_data = {
            "schemaVersion": project.schema_version,
            "metadata": {
                "id": f"lab_{project.id}",
                "title": project.title,
                "author": project.author,
                "description": project.description or "",
                "created": project.created_at.isoformat(),
                "tags": project.tags.split(",") if project.tags else []
            },
            "canvas": canvas,
            "ingredients": ingredients,
            "tutorial": tutorial,
            "providerHints": {
                "linux": "libvirt",
                "windows": "hyperv"
            }
        }
        
        return lab_data
    
    def _create_zip(self, source_dir: Path, zip_path: Path):
        """
        Create ZIP file from directory
        
        Args:
            source_dir: Source directory to ZIP
            zip_path: Destination ZIP file path
        """
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(source_dir)
                    zipf.write(file_path, arcname)
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for safe file system usage
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Replace spaces with underscores
        filename = filename.replace(" ", "_")
        
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, "")
        
        # Limit length
        if len(filename) > 200:
            filename = filename[:200]
        
        return filename
