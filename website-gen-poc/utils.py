"""
Utility functions for the frontend generator
"""

import time
import os
from pathlib import Path

def generate_unique_project_name(base_name: str) -> str:
    """
    Generate a unique project name with timestamp to avoid conflicts
    
    Args:
        base_name: The base name for the project (e.g., "personal-blog")
        
    Returns:
        Unique project name with timestamp (e.g., "personal-blog-1703123456")
    """
    timestamp = int(time.time())
    return f"{base_name}-{timestamp}"

def ensure_unique_directory(base_path: str, project_name: str) -> str:
    """
    Ensure a unique directory path by appending timestamp if needed
    
    Args:
        base_path: Base directory path (e.g., "generated_projects")
        project_name: Project name
        
    Returns:
        Unique directory path
    """
    unique_name = generate_unique_project_name(project_name)
    return os.path.join(base_path, unique_name)

def list_generated_projects() -> list:
    """
    List all generated projects in the generated_projects directory
    
    Returns:
        List of project directory names
    """
    projects_dir = Path("generated_projects")
    if not projects_dir.exists():
        return []
    
    return [d.name for d in projects_dir.iterdir() if d.is_dir()]

def get_project_info(project_name: str) -> dict:
    """
    Get information about a specific generated project
    
    Args:
        project_name: Name of the project directory
        
    Returns:
        Dictionary with project information
    """
    project_path = Path("generated_projects") / project_name
    
    if not project_path.exists():
        return {"error": "Project not found"}
    
    info = {
        "name": project_name,
        "path": str(project_path.absolute()),
        "created": project_path.stat().st_ctime,
        "files": []
    }
    
    # Count files
    for file_path in project_path.rglob("*"):
        if file_path.is_file():
            info["files"].append({
                "name": file_path.name,
                "path": str(file_path.relative_to(project_path)),
                "size": file_path.stat().st_size
            })
    
    # Try to get package.json info
    package_json = project_path / "package.json"
    if package_json.exists():
        try:
            import json
            with open(package_json, 'r') as f:
                package_data = json.load(f)
                info["package"] = {
                    "name": package_data.get("name"),
                    "version": package_data.get("version"),
                    "description": package_data.get("description")
                }
        except:
            pass
    
    return info 