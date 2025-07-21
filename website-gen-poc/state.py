from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from enum import Enum

class ProjectType(str, Enum):
    BLOG = "blog"
    PORTFOLIO = "portfolio"
    ECOMMERCE = "ecommerce"
    DASHBOARD = "dashboard"
    LANDING_PAGE = "landing_page"
    OTHER = "other"

class ComponentSpec(BaseModel):
    name: str
    purpose: str
    props: Dict[str, str]
    children: List[str] = []
    styling_requirements: str = ""

class ProjectSpec(BaseModel):
    name: str
    type: ProjectType
    description: str
    components: List[ComponentSpec] = []
    dependencies: List[str] = []
    styling_framework: str = "tailwind"
    features: List[str] = []

class GeneratedFile(BaseModel):
    path: str
    content: str
    file_type: str

class WorkflowState(BaseModel):
    # Input
    user_request: str = ""
    
    # Analysis results
    project_spec: Optional[ProjectSpec] = None
    architecture_plan: Dict[str, Any] = {}
    
    # Generated content
    generated_files: List[GeneratedFile] = []
    project_structure: Dict[str, Any] = {}
    
    # Status tracking
    completed_steps: List[str] = []
    current_step: str = ""
    errors: List[str] = []
    
    # Output
    output_directory: str = ""
    ready_to_run: bool = False
    
    class Config:
        arbitrary_types_allowed = True
        # Add LangGraph compatibility
        extra = "allow"
        validate_assignment = True 