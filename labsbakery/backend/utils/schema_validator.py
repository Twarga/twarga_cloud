"""
🧁 LabsBakery Core - Schema Validator
Validates lab packages against JSON schema
"""
import json
import jsonschema
from typing import Dict, List
from pathlib import Path


class SchemaValidator:
    """Validates lab JSON data against the LabsBakery schema"""
    
    def __init__(self, schema_path: str = "lab_schema.json"):
        """
        Initialize validator with schema file
        
        Args:
            schema_path: Path to JSON schema file
        """
        self.schema_path = Path(schema_path)
        self.schema = self._load_schema()
    
    def _load_schema(self) -> Dict:
        """Load JSON schema from file"""
        try:
            with open(self.schema_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in schema file: {e}")
    
    def validate(self, lab_data: Dict) -> Dict[str, any]:
        """
        Validate lab JSON against schema
        
        Args:
            lab_data: Lab data dictionary to validate
            
        Returns:
            Dictionary with validation results:
            {
                "valid": bool,
                "errors": List[str],
                "warnings": List[str]
            }
        """
        errors = []
        warnings = []
        
        try:
            # Validate against schema
            jsonschema.validate(lab_data, self.schema)
            
            # Additional custom validations
            custom_warnings = self._custom_validations(lab_data)
            warnings.extend(custom_warnings)
            
            return {
                "valid": True,
                "errors": [],
                "warnings": warnings
            }
            
        except jsonschema.ValidationError as e:
            # Extract error message and path
            error_path = ".".join(str(p) for p in e.path) if e.path else "root"
            error_msg = f"{error_path}: {e.message}"
            errors.append(error_msg)
            
            return {
                "valid": False,
                "errors": errors,
                "warnings": warnings
            }
        
        except jsonschema.SchemaError as e:
            return {
                "valid": False,
                "errors": [f"Schema error: {e.message}"],
                "warnings": []
            }
    
    def _custom_validations(self, lab_data: Dict) -> List[str]:
        """
        Perform additional custom validations beyond JSON schema
        
        Args:
            lab_data: Lab data dictionary
            
        Returns:
            List of warning messages
        """
        warnings = []
        
        # Check if lab has any VMs
        ingredients = lab_data.get("ingredients", [])
        if len(ingredients) == 0:
            warnings.append("Lab has no VMs defined")
        
        # Check if lab has too many VMs
        if len(ingredients) > 10:
            warnings.append(f"Lab has {len(ingredients)} VMs, which may be resource-intensive")
        
        # Check total RAM requirements
        total_ram = sum(ing.get("ram", 2048) for ing in ingredients)
        if total_ram > 8192:  # More than 8GB
            warnings.append(
                f"Lab requires {total_ram}MB RAM total, "
                f"which may exceed typical system resources"
            )
        
        # Check if tutorial exists
        tutorial = lab_data.get("tutorial", {})
        if not tutorial or not tutorial.get("steps"):
            warnings.append("Lab has no tutorial steps defined")
        
        return warnings
    
    def validate_file(self, file_path: str) -> Dict[str, any]:
        """
        Validate a JSON file
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Validation results dictionary
        """
        try:
            with open(file_path, "r") as f:
                lab_data = json.load(f)
            return self.validate(lab_data)
        except FileNotFoundError:
            return {
                "valid": False,
                "errors": [f"File not found: {file_path}"],
                "warnings": []
            }
        except json.JSONDecodeError as e:
            return {
                "valid": False,
                "errors": [f"Invalid JSON: {e}"],
                "warnings": []
            }


def validate_lab(lab_data: Dict) -> Dict[str, any]:
    """
    Convenience function to validate lab data
    
    Args:
        lab_data: Lab data dictionary
        
    Returns:
        Validation results
    """
    validator = SchemaValidator()
    return validator.validate(lab_data)
