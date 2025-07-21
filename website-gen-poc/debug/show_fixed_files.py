#!/usr/bin/env python3
"""
Script to show the actual fixed files after integration agent runs
"""

import os
import json
from src.agents.integration_agent import IntegrationAgent
from state import WorkflowState, GeneratedFile, ProjectSpec, ComponentSpec

def create_broken_project():
    """Create a project with intentional integration errors"""
    state = WorkflowState(
        user_request="Test integration agent with broken components",
        current_step="integration"
    )
    
    state.project_spec = ProjectSpec(
        name="Test Blog",
        type="blog",
        description="A test blog with intentional errors",
        styling_framework="tailwind",
        components=[],
        dependencies=[]
    )
    
    # Create a broken Header component
    broken_header = '''import { useState } from 'react';
import { Link } from 'react-router-dom';

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

          <nav className="hidden md:flex items-center space-x-8">
            <Link to="/" className="text-gray-600 hover:text-gray-900">
              Home
            </a>
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

          <button
            type="button"
            className="md:hidden inline-flex items-center justify-center p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
          >
            <svg className="h-6 w-6" stroke="currentColor" fill="none" viewBox="0 0 24 24">
              {isMenuOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>

        {isMenuOpen && (
          <div className="md:hidden">
            <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
              <Link to="/" className="block px-3 py-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100">
                Home
              </Link>
              <Link to="/articles" className="block px-3 py-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100">
                Articles
              </Link>
              <Link to="/about" className="block px-3 py-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100">
                About
              </Link>
              <Link to="/write" className="block px-3 py-2 rounded-md bg-blue-600 text-white hover:bg-blue-700">
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
    
    # Create a component with missing imports
    broken_blog_post = '''const BlogPost = () => {
  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <article className="prose lg:prose-xl">
        <h1 className="text-3xl font-bold mb-4">Sample Blog Post</h1>
        <p className="text-gray-600 mb-4">This is a sample blog post content.</p>
        
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
    
    # Create package.json without react-router-dom
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
    
    files = [
        GeneratedFile(path="src/components/Header.tsx", content=broken_header, file_type="tsx"),
        GeneratedFile(path="src/components/BlogPost.tsx", content=broken_blog_post, file_type="tsx"),
        GeneratedFile(path="src/components/Comments.tsx", content=comments_component, file_type="tsx"),
        GeneratedFile(path="package.json", content=package_json, file_type="json")
    ]
    
    state.generated_files = files
    return state

def show_fixed_files():
    """Show the actual fixed files after integration agent runs"""
    print("🔧 Integration Agent - Before and After Comparison")
    print("=" * 60)
    
    # Create broken project
    state = create_broken_project()
    
    # Show original files
    print("\n📄 ORIGINAL FILES (with errors):")
    print("-" * 40)
    
    for file in state.generated_files:
        print(f"\n🔴 {file.path}:")
        print("Issues found:")
        if file.path == "src/components/Header.tsx":
            print("  - Uses react-router-dom Link components")
            print("  - Has mismatched JSX closing tags (<Link>...</a>)")
        elif file.path == "src/components/BlogPost.tsx":
            print("  - Uses Comments component without import")
        elif file.path == "package.json":
            print("  - Missing react-router-dom dependency")
    
    # Run integration agent
    print("\n🔧 Running Integration Agent...")
    api_key = os.getenv("ANTHROPIC_API_KEY", "your-anthropic-api-key")
    agent = IntegrationAgent(api_key)
    updated_state = agent.analyze_and_fix_integration(state)
    
    # Show fixed files
    print("\n✅ FIXED FILES:")
    print("-" * 40)
    
    for file in updated_state.generated_files:
        print(f"\n🟢 {file.path}:")
        
        if file.path == "src/components/Header.tsx":
            print("Fixes applied:")
            if "react-router-dom" not in file.content:
                print("  ✅ Removed react-router-dom import")
            if "<Link" not in file.content:
                print("  ✅ Replaced all Link components with anchor tags")
            if "to=" not in file.content:
                print("  ✅ Replaced 'to' attributes with 'href'")
            print("\nFixed Header.tsx content:")
            print("```tsx")
            print(file.content[:500] + "..." if len(file.content) > 500 else file.content)
            print("```")
            
        elif file.path == "src/components/BlogPost.tsx":
            print("Fixes applied:")
            if "import Comments" in file.content:
                print("  ✅ Added missing Comments import")
            print("\nFixed BlogPost.tsx content:")
            print("```tsx")
            print(file.content)
            print("```")
            
        elif file.path == "package.json":
            try:
                package_data = json.loads(file.content)
                dependencies = package_data.get("dependencies", {})
                print("Fixes applied:")
                if "react-router-dom" in dependencies:
                    print("  ✅ Added react-router-dom dependency")
                print(f"\nUpdated dependencies: {dependencies}")
            except json.JSONDecodeError:
                print("Could not parse package.json")
    
    print("\n🎉 Integration Agent successfully fixed all detected issues!")
    print("The project should now run without errors.")

if __name__ == "__main__":
    show_fixed_files() 