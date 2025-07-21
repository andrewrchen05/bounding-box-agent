#!/usr/bin/env python3
"""
Test script to demonstrate the integration agent fixing component integration issues
"""

import os
import json
from src.agents.integration_agent import IntegrationAgent
from state import WorkflowState, GeneratedFile, ProjectSpec, ComponentSpec

def load_existing_project():
    """Load the existing personal blog project files"""
    project_dir = "generated_projects/personal-blog"
    state = WorkflowState(
        user_request="Fix integration issues in personal blog",
        current_step="integration"
    )
    
    # Create a basic project spec
    state.project_spec = ProjectSpec(
        name="Personal Blog",
        type="blog",
        description="A modern personal blog with React and TypeScript",
        styling_framework="tailwind",
        components=[],
        dependencies=[]
    )
    
    # Load existing files
    files_to_load = [
        "src/App.tsx",
        "src/main.tsx", 
        "src/components/Header.tsx",
        "src/components/BlogPost.tsx",
        "src/components/PostList.tsx",
        "src/components/Comments.tsx",
        "package.json",
        "vite.config.ts",
        "tsconfig.json"
    ]
    
    for file_path in files_to_load:
        full_path = os.path.join(project_dir, file_path)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            file_type = file_path.split('.')[-1]
            generated_file = GeneratedFile(
                path=file_path,
                content=content,
                file_type=file_type
            )
            state.generated_files.append(generated_file)
    
    return state

def test_integration_agent():
    """Test the integration agent on the existing project"""
    print("Loading existing personal blog project...")
    state = load_existing_project()
    
    print(f"Found {len(state.generated_files)} files")
    for file in state.generated_files:
        print(f"  - {file.path}")
    
    # Initialize integration agent
    api_key = os.getenv("ANTHROPIC_API_KEY", "your-anthropic-api-key")
    agent = IntegrationAgent(api_key)
    
    print("\nAnalyzing integration issues...")
    updated_state = agent.analyze_and_fix_integration(state)
    
    print(f"\nIntegration analysis complete!")
    print(f"Completed steps: {updated_state.completed_steps}")
    
    if updated_state.errors:
        print(f"Errors: {updated_state.errors}")
    
    # Show what files were updated
    print(f"\nUpdated {len(updated_state.generated_files)} files")
    
    # Check if package.json was updated with missing dependencies
    package_file = None
    for file in updated_state.generated_files:
        if file.path == "package.json":
            package_file = file
            break
    
    if package_file:
        try:
            package_data = json.loads(package_file.content)
            dependencies = package_data.get("dependencies", {})
            print(f"\nDependencies in package.json:")
            for dep, version in dependencies.items():
                print(f"  - {dep}: {version}")
        except json.JSONDecodeError:
            print("Could not parse package.json")
    
    return updated_state

if __name__ == "__main__":
    test_integration_agent() 