#!/usr/bin/env python3
"""
Script to fix the personal blog project and get it running on localhost
"""

import os
import json
import subprocess
import sys

def fix_package_json():
    """Add missing dependencies to package.json"""
    package_path = "generated_projects/personal-blog/package.json"
    
    with open(package_path, 'r') as f:
        package_data = json.load(f)
    
    # Add missing dependencies
    if "dependencies" not in package_data:
        package_data["dependencies"] = {}
    
    # Add react-router-dom if not present
    if "react-router-dom" not in package_data["dependencies"]:
        package_data["dependencies"]["react-router-dom"] = "^6.0.0"
    
    # Add @heroicons/react if needed
    if "@heroicons/react" not in package_data["dependencies"]:
        package_data["dependencies"]["@heroicons/react"] = "^2.0.0"
    
    with open(package_path, 'w') as f:
        json.dump(package_data, f, indent=2)
    
    print("✅ Updated package.json with missing dependencies")

def fix_header_component():
    """Fix the Header component to work without react-router-dom for now"""
    header_path = "generated_projects/personal-blog/src/components/Header.tsx"
    
    with open(header_path, 'r') as f:
        content = f.read()
    
    # Remove react-router-dom imports and replace with simple navigation
    content = content.replace(
        "import { Link } from 'react-router-dom'",
        "// import { Link } from 'react-router-dom'"
    )
    
    # Replace Link components with simple anchor tags
    content = content.replace(
        '<Link to="/"',
        '<a href="#"'
    )
    content = content.replace(
        '<Link to="/blog"',
        '<a href="#"'
    )
    content = content.replace(
        '<Link to="/about"',
        '<a href="#"'
    )
    content = content.replace(
        '</Link>',
        '</a>'
    )
    
    with open(header_path, 'w') as f:
        f.write(content)
    
    print("✅ Fixed Header component imports")

def install_dependencies():
    """Install npm dependencies"""
    os.chdir("generated_projects/personal-blog")
    
    print("Installing dependencies...")
    result = subprocess.run(["npm", "install"], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Dependencies installed successfully")
    else:
        print(f"❌ Failed to install dependencies: {result.stderr}")
        return False
    
    return True

def start_dev_server():
    """Start the development server"""
    print("Starting development server...")
    
    # Start the server in the background
    process = subprocess.Popen(
        ["npm", "run", "dev"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait a moment for the server to start
    import time
    time.sleep(3)
    
    # Check if the process is still running
    if process.poll() is None:
        print("✅ Development server started successfully!")
        print("🌐 Your personal blog is now running at: http://localhost:3000")
        print("Press Ctrl+C to stop the server")
        
        try:
            # Keep the script running
            process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping development server...")
            process.terminate()
    else:
        stdout, stderr = process.communicate()
        print(f"❌ Failed to start development server:")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")

def main():
    """Main function to fix and run the personal blog"""
    print("🔧 Fixing Personal Blog Project")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not os.path.exists("generated_projects/personal-blog"):
        print("❌ Personal blog project not found!")
        print("Please run this script from the project root directory")
        sys.exit(1)
    
    # Fix package.json
    fix_package_json()
    
    # Fix Header component
    fix_header_component()
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Start development server
    start_dev_server()

if __name__ == "__main__":
    main() 