#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced integration agent's ability to catch and fix errors
"""

import os
import json
from src.agents.integration_agent import IntegrationAgent
from state import WorkflowState, GeneratedFile, ProjectSpec, ComponentSpec

def create_broken_project():
    """Create a project with intentional integration errors to test the agent"""
    state = WorkflowState(
        user_request="Test integration agent with broken components",
        current_step="integration"
    )
    
    # Create a basic project spec
    state.project_spec = ProjectSpec(
        name="Test Blog",
        type="blog",
        description="A test blog with intentional errors",
        styling_framework="tailwind",
        components=[],
        dependencies=[]
    )
    
    # Create a broken Header component with JSX errors
    broken_header = '''import { useState } from 'react';
import { Link } from 'react-router-dom';  // This will cause issues

const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 bg-white shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="flex justify-between items-center py-4">
          <div className="flex items-center">
            <Link to="/" className="text-2xl font-bold text-gray-900 hover:text-gray-700">
              MyBlog
            </Link>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-8">
            <Link to="/" className="text-gray-600 hover:text-gray-900">
              Home
            </a>  {/* Mismatched closing tag */}
            <Link to="/articles" className="text-gray-600 hover:text-gray-900">
              Articles
            </Link>
            <Link to="/about" className="text-gray-600 hover:text-gray-900">
              About
            </Link>
            <Link 
              to="/write" 
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
            >
              Write Article
            </Link>
          </nav>

          {/* Mobile menu button */}
          <button
            type="button"
            className="md:hidden inline-flex items-center justify-center p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            aria-expanded="false"
            aria-label="Toggle navigation"
          >
            <svg
              className="h-6 w-6"
              stroke="currentColor"
              fill="none"
              viewBox="0 0 24 24"
            >
              {isMenuOpen ? (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M6 18L18 6M6 6l12 12"
                />
              ) : (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M4 6h16M4 12h16M4 18h16"
                />
              )}
            </svg>
          </button>
        </div>

        {/* Mobile Navigation */}
        {isMenuOpen && (
          <div className="md:hidden">
            <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
              <Link
                to="/"
                className="block px-3 py-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100"
              >
                Home
              </Link>
              <Link
                to="/articles"
                className="block px-3 py-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100"
              >
                Articles
              </Link>
              <Link
                to="/about"
                className="block px-3 py-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100"
              >
                About
              </Link>
              <Link
                to="/write"
                className="block px-3 py-2 rounded-md bg-blue-600 text-white hover:bg-blue-700"
              >
                Write Article
              </Link>
            </div>
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;'''
    
    # Create a component that references undefined components
    broken_blog_post = '''const BlogPost = () => {
  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <article className="prose lg:prose-xl">
        <h1 className="text-3xl font-bold mb-4">Sample Blog Post</h1>
        <p className="text-gray-600 mb-4">This is a sample blog post content.</p>
        
        {/* This component doesn't exist and will cause an error */}
        <UndefinedComponent />
        
        {/* This component exists but isn't imported */}
        <Comments />
      </article>
    </div>
  );
};

export default BlogPost;'''
    
    # Create a Comments component
    comments_component = '''import React from 'react';

const Comments = () => {
  return (
    <div className="mt-8">
      <h3 className="text-xl font-semibold mb-4">Comments</h3>
      <div className="space-y-4">
        <div className="bg-gray-50 p-4 rounded-lg">
          <p className="text-gray-800">Great article!</p>
          <p className="text-sm text-gray-500 mt-2">- John Doe</p>
        </div>
      </div>
    </div>
  );
};

export default Comments;'''
    
    # Create a package.json without react-router-dom
    package_json = '''{
  "name": "test-blog",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.66",
    "@types/react-dom": "^18.2.22",
    "@vitejs/plugin-react": "^4.2.1",
    "typescript": "^5.2.2",
    "vite": "^5.2.0",
    "tailwindcss": "^3.4.3",
    "autoprefixer": "^10.4.19",
    "postcss": "^8.4.38"
  }
}'''
    
    # Add files to state
    files = [
        GeneratedFile(path="src/components/Header.tsx", content=broken_header, file_type="tsx"),
        GeneratedFile(path="src/components/BlogPost.tsx", content=broken_blog_post, file_type="tsx"),
        GeneratedFile(path="src/components/Comments.tsx", content=comments_component, file_type="tsx"),
        GeneratedFile(path="package.json", content=package_json, file_type="json")
    ]
    
    state.generated_files = files
    return state

def test_enhanced_integration_agent():
    """Test the enhanced integration agent on a broken project"""
    print("🧪 Testing Enhanced Integration Agent")
    print("=" * 50)
    
    # Create a project with intentional errors
    print("Creating test project with intentional errors...")
    state = create_broken_project()
    
    print(f"Created {len(state.generated_files)} files with known issues:")
    for file in state.generated_files:
        print(f"  - {file.path}")
    
    print("\n🔍 Known issues in the test project:")
    print("  - Header.tsx: Uses react-router-dom Link components")
    print("  - Header.tsx: Has mismatched JSX closing tags")
    print("  - BlogPost.tsx: References undefined component 'UndefinedComponent'")
    print("  - BlogPost.tsx: Uses Comments component without import")
    print("  - package.json: Missing react-router-dom dependency")
    
    # Initialize integration agent
    api_key = os.getenv("ANTHROPIC_API_KEY", "your-anthropic-api-key")
    agent = IntegrationAgent(api_key)
    
    print("\n🔧 Running enhanced integration agent...")
    updated_state = agent.analyze_and_fix_integration(state)
    
    print(f"\n✅ Integration analysis complete!")
    print(f"Completed steps: {updated_state.completed_steps}")
    
    if updated_state.errors:
        print(f"❌ Errors: {updated_state.errors}")
    
    # Show what was fixed
    print(f"\n📝 Analysis of fixes applied:")
    
    # Check Header component
    header_file = None
    for file in updated_state.generated_files:
        if file.path == "src/components/Header.tsx":
            header_file = file
            break
    
    if header_file:
        print("\n🔧 Header.tsx fixes:")
        if "react-router-dom" not in header_file.content:
            print("  ✅ Removed react-router-dom imports")
        if "<Link" not in header_file.content:
            print("  ✅ Replaced Link components with anchor tags")
        if "mismatched" not in header_file.content.lower():
            print("  ✅ Fixed JSX tag mismatches")
    
    # Check BlogPost component
    blog_post_file = None
    for file in updated_state.generated_files:
        if file.path == "src/components/BlogPost.tsx":
            blog_post_file = file
            break
    
    if blog_post_file:
        print("\n🔧 BlogPost.tsx fixes:")
        if "UndefinedComponent" not in blog_post_file.content:
            print("  ✅ Removed undefined component reference")
        if "import Comments" in blog_post_file.content:
            print("  ✅ Added missing Comments import")
    
    # Check package.json
    package_file = None
    for file in updated_state.generated_files:
        if file.path == "package.json":
            package_file = file
            break
    
    if package_file:
        try:
            package_data = json.loads(package_file.content)
            dependencies = package_data.get("dependencies", {})
            print(f"\n📦 Package.json dependencies:")
            for dep, version in dependencies.items():
                print(f"  - {dep}: {version}")
        except json.JSONDecodeError:
            print("Could not parse package.json")
    
    return updated_state

if __name__ == "__main__":
    test_enhanced_integration_agent() 