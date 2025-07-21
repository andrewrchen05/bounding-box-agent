#!/usr/bin/env python3
"""
Demo test script to showcase the agent architecture without requiring OpenAI API key.
This creates a mock workflow that shows how the system would work.
"""

import json
from state import WorkflowState, ProjectSpec, ProjectType, ComponentSpec, GeneratedFile
from src.agents.integration_agent import IntegrationAgent

def mock_requirements_analysis(user_request: str) -> ProjectSpec:
    """Mock requirements analysis for demo purposes"""
    print(f"🔍 Requirements Agent analyzing: '{user_request}'")
    
    # Mock analysis based on request
    if "blog" in user_request.lower():
        components = [
            ComponentSpec(
                name="Header",
                purpose="Navigation and site branding",
                props={"logo": "string", "navItems": "array"},
                styling_requirements="Fixed header with navigation menu"
            ),
            ComponentSpec(
                name="BlogPost",
                purpose="Display individual blog post content",
                props={"title": "string", "content": "string", "date": "string", "author": "string"},
                styling_requirements="Clean typography with good readability"
            ),
            ComponentSpec(
                name="BlogList",
                purpose="List of blog posts with previews",
                props={"posts": "array"},
                children=["BlogPost"],
                styling_requirements="Grid layout with post previews"
            ),
            ComponentSpec(
                name="Footer",
                purpose="Site footer with links and info",
                props={"links": "array", "copyright": "string"},
                styling_requirements="Simple footer with social links"
            )
        ]
        
        return ProjectSpec(
            name="Personal Blog",
            type=ProjectType.BLOG,
            description="A clean, modern personal blog with responsive design",
            components=components,
            dependencies=["react", "react-dom", "@types/react", "@types/react-dom"],
            styling_framework="tailwind",
            features=["responsive-design", "blog-posts", "navigation", "clean-typography"]
        )
    
    # Default fallback
    return ProjectSpec(
        name="Simple Website",
        type=ProjectType.OTHER,
        description="A basic website",
        components=[],
        styling_framework="tailwind"
    )

def mock_component_generation(project_spec: ProjectSpec) -> list[GeneratedFile]:
    """Mock component generation for demo purposes"""
    print("⚛️  Component Agent generating React components...")
    
    generated_files = []
    
    # Generate mock components
    for component in project_spec.components:
        component_code = f'''import React from 'react';

interface {component.name}Props {{
  // Props would be generated based on specification
  className?: string;
}}

const {component.name}: React.FC<{component.name}Props> = ({{
  className = "",
  ...props
}}) => {{
  return (
    <div className={{`{component.name.lower()}-component ${{className}}`}}>
      <h2>This is the {component.name} component</h2>
      <p>Purpose: {component.purpose}</p>
      {{/* Component implementation would be generated here */}}
    </div>
  );
}};

export default {component.name};'''
        
        generated_files.append(GeneratedFile(
            path=f"src/components/{component.name}.tsx",
            content=component_code,
            file_type="tsx"
        ))
    
    # Generate App.tsx
    component_imports = "\n".join([
        f"import {comp.name} from './components/{comp.name}'"
        for comp in project_spec.components
    ])
    
    component_usage = "\n".join([
        f"        <{comp.name} />"
        for comp in project_spec.components
    ])
    
    app_code = f'''import React from 'react'
import './App.css'
{component_imports}

function App() {{
  return (
    <div className="App min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold text-center mb-8 text-gray-800">
          {project_spec.name}
        </h1>
{component_usage}
      </div>
    </div>
  )
}}

export default App'''
    
    generated_files.append(GeneratedFile(
        path="src/App.tsx",
        content=app_code,
        file_type="tsx"
    ))
    
    # Generate main.tsx
    main_code = '''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)'''
    
    generated_files.append(GeneratedFile(
        path="src/main.tsx",
        content=main_code,
        file_type="tsx"
    ))
    
    return generated_files

def demo_workflow(user_request: str = "Create a dating app"):
    """Demonstrate the complete workflow without API calls"""
    
    print("🚀 Frontend Generation Agent POC Demo")
    print("=" * 50)
    print(f"User Request: '{user_request}'")
    print()
    
    # Step 1: Requirements Analysis
    project_spec = mock_requirements_analysis(user_request)
    print(f"✅ Project Spec: {project_spec.name} ({project_spec.type})")
    print(f"   Components: {[comp.name for comp in project_spec.components]}")
    print()
    
    # Step 2: Architecture Planning
    print("🏗️  Architecture Agent planning project structure...")
    architecture_plan = {
        "build_tool": "vite",
        "project_structure": {
            "src/": {
                "components/": {},
                "App.tsx": {},
                "main.tsx": {},
                "index.css": {}
            },
            "public/": {},
            "package.json": {},
            "vite.config.ts": {},
            "tsconfig.json": {}
        }
    }
    print("✅ Architecture planned with Vite + React + TypeScript + Tailwind")
    print()
    
    # Step 3: Component Generation
    generated_files = mock_component_generation(project_spec)
    print(f"✅ Generated {len(generated_files)} component files")
    print()
    
    # Step 4: Integration
    print("🔧 Integration Agent assembling project...")
    
    # Create workflow state
    state = WorkflowState(
        user_request=user_request,
        project_spec=project_spec,
        architecture_plan=architecture_plan,
        generated_files=generated_files
    )
    
    # Use real integration agent to generate config files
    integration_agent = IntegrationAgent()
    final_state = integration_agent.integrate_project(state)
    
    # Don't actually create files in demo, just show what would be created
    print(f"✅ Integration complete! Would create {len(final_state.generated_files)} total files:")
    
    # Show file structure
    files_by_dir = {}
    for file in final_state.generated_files:
        dir_name = file.path.split('/')[0] if '/' in file.path else "root"
        if dir_name not in files_by_dir:
            files_by_dir[dir_name] = []
        files_by_dir[dir_name].append(file.path)
    
    print(f"\n📁 Project Structure for '{project_spec.name}':")
    for dir_name, files in files_by_dir.items():
        print(f"  {dir_name}/")
        for file_path in files:
            if dir_name != "root":
                relative_path = file_path[len(dir_name)+1:]
                print(f"    {relative_path}")
            else:
                print(f"    {file_path}")
    
    print(f"\n🎯 Demo complete! This shows how the LangGraph workflow would:")
    print("   1. Analyze requirements → Project specification")
    print("   2. Plan architecture → File structure and build config") 
    print("   3. Generate components → React/TypeScript code")
    print("   4. Integrate everything → Complete runnable project")
    print()
    print("💡 To run with real Anthropic API:")
    print("   1. Set ANTHROPIC_API_KEY environment variable")
    print("   2. Run: python3 main.py 'Create a personal blog'")
    
    return final_state

if __name__ == "__main__":
    # Run the demo
    demo_workflow() 