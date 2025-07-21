#!/usr/bin/env python3
"""
Frontend Generation Agent POC

A simplified agent architecture that generates complete TypeScript/React projects
from high-level user requests.

Two generation modes available:
- Default: Multi-agent workflow (requirements → architecture → components → integration)
- --single-context: Generate entire project in one comprehensive pass

Usage:
    python main.py "Create a personal blog"
    python main.py "Build a portfolio website"
    python main.py --single-context "Create a personal blog"
    python main.py --debug "Create a personal blog"
    python main.py --cleanup [project_name]
    python main.py --list-projects
"""

import sys
import os
import shutil
from pathlib import Path
from dotenv import load_dotenv
from src.workflows.workflow_pydantic_compatible import generate_frontend_project
from src.generators.single_context_generator import generate_frontend_project_single_context
from state import WorkflowState
from utils import list_generated_projects, get_project_info

def main():
    """Main entry point for the frontend generator"""
    
    # Load environment variables
    load_dotenv()
    
    # Check for flags and commands
    single_context_mode = False
    debug_mode = False
    if len(sys.argv) > 1:
        if sys.argv[1] == "--cleanup":
            return cleanup_projects(sys.argv[2] if len(sys.argv) > 2 else None)
        elif sys.argv[1] == "--list-projects":
            return list_projects()

        elif sys.argv[1] == "--single-context":
            single_context_mode = True
            # Remove the flag from args so the rest of the request is processed normally
            sys.argv.pop(1)
        elif sys.argv[1] == "--debug":
            debug_mode = True
            # Remove the flag from args so the rest of the request is processed normally
            sys.argv.pop(1)
    
    return generate_project(single_context_mode, debug_mode)

def generate_project(single_context_mode=False, debug_mode=False):
    """Generate a frontend project"""
    # Get Anthropic API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        print("Please set your Anthropic API key in a .env file or environment variable")
        print("Example .env file content:")
        print("ANTHROPIC_API_KEY=your-api-key-here")
        return 1
    
    # Get user request
    if len(sys.argv) > 1:
        user_request = " ".join(sys.argv[1:])
    else:
        print("Enter your frontend project request:")
        user_request = input("> ")
    
    if not user_request.strip():
        print("❌ Error: No request provided")
        return 1
    
    mode_text = "single context" if single_context_mode else "multi-agent workflow"
    print(f"\n🚀 Generating frontend for: '{user_request}' (using {mode_text})")
    if debug_mode:
        print("🐛 Debug mode enabled - detailed logging will be shown")
    print("This may take a few minutes...")
    
    try:
        # Generate the project using the appropriate method
        if single_context_mode:
            state = generate_frontend_project_single_context(user_request, api_key)
        else:
            state = generate_frontend_project(user_request, api_key)
        
        if state.ready_to_run and not state.errors:
            print(f"\n✅ Success! Your project has been generated.")
            print(f"📁 Location: {state.output_directory}")
            print(f"📄 Files created: {len(state.generated_files)}")
            
            # Ask if user wants to automatically install dependencies and start
            if input("\n🔧 Install dependencies and start development server? (y/n): ").lower() == 'y':
                start_project(state.output_directory)
        else:
            print(f"\n❌ Generation failed:")
            if state.errors:
                for error in state.errors:
                    print(f"  - {error}")
            return 1
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        return 1
    
    return 0

def cleanup_projects(project_name: str = None):
    """Clean up generated projects"""
    generated_dir = Path("generated_projects")
    
    if not generated_dir.exists():
        print("📁 No generated projects directory found")
        return 0
    
    if project_name:
        # Clean up specific project
        project_path = generated_dir / project_name
        if not project_path.exists():
            print(f"❌ Project '{project_name}' not found")
            return 1
        
        try:
            shutil.rmtree(project_path)
            print(f"✅ Removed project: {project_name}")
        except Exception as e:
            print(f"❌ Error removing project '{project_name}': {str(e)}")
            return 1
    else:
        # Clean up all projects
        projects = list(generated_dir.iterdir())
        if not projects:
            print("📁 No projects to clean up")
            return 0
        
        print(f"🗑️  Found {len(projects)} project(s) to remove:")
        for project in projects:
            if project.is_dir():
                print(f"  - {project.name}")
        
        confirm = input("\n⚠️  Are you sure you want to remove all projects? (y/N): ")
        if confirm.lower() != 'y':
            print("❌ Cleanup cancelled")
            return 0
        
        try:
            shutil.rmtree(generated_dir)
            print("✅ All projects removed successfully")
        except Exception as e:
            print(f"❌ Error removing projects: {str(e)}")
            return 1
    
    return 0

def list_projects():
    """List all generated projects"""
    projects = list_generated_projects()
    
    if not projects:
        print("📁 No projects found")
        return 0
    
    print(f"📁 Found {len(projects)} project(s):")
    for project_name in projects:
        # Get detailed project info
        info = get_project_info(project_name)
        
        if "error" in info:
            print(f"  📁 {project_name} (error: {info['error']})")
        else:
            # Format creation time
            import datetime
            created_time = datetime.datetime.fromtimestamp(info["created"]).strftime("%Y-%m-%d %H:%M:%S")
            
            if "package" in info and info["package"]:
                package = info["package"]
                name = package.get("name", project_name)
                version = package.get("version", "N/A")
                description = package.get("description", "")
                print(f"  📦 {name} (v{version}) - {project_name}")
                if description:
                    print(f"     📝 {description}")
            else:
                print(f"  📁 {project_name}")
            
            print(f"     🕒 Created: {created_time}")
            print(f"     📄 Files: {len(info['files'])}")
    
    return 0

def start_project(project_dir: str):
    """Install dependencies and start the development server"""
    import subprocess
    
    try:
        print(f"\n📦 Installing dependencies in {project_dir}...")
        
        # Change to project directory
        os.chdir(project_dir)
        
        # Install dependencies
        result = subprocess.run(["npm", "install"], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ npm install failed: {result.stderr}")
            return
        
        print("✅ Dependencies installed successfully!")
        print("\n🚀 Starting development server...")
        print("Opening http://localhost:3000 in your browser...")
        
        # Start development server
        subprocess.run(["npm", "run", "dev"])
        
    except FileNotFoundError:
        print("❌ npm not found. Please install Node.js and npm first.")
        print("Then run:")
        print(f"  cd {project_dir}")
        print("  npm install")
        print("  npm run dev")
    except Exception as e:
        print(f"❌ Error starting project: {str(e)}")



if __name__ == "__main__":
    exit(main()) 