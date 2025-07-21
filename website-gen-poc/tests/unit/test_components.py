#!/usr/bin/env python3
"""
Test script for component generation step
"""

import os
import json
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate

def test_component_generation():
    """Test the component generation step"""
    
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        return False
    
    # Initialize LLM
    llm = ChatAnthropic(
        model="claude-3-5-sonnet-20241022",
        anthropic_api_key=api_key,
        temperature=0.2
    )
    
    # Sample project spec (from requirements analysis)
    project_spec = {
        "name": "personal-blog",
        "type": "blog",
        "description": "A personal blog platform for publishing and managing articles",
        "components": [
            {
                "name": "Header",
                "purpose": "Main navigation and blog title",
                "props": {"title": "string", "navItems": "array"},
                "children": ["NavMenu", "SearchBar"],
                "styling": "Sticky header with responsive design"
            },
            {
                "name": "BlogPost",
                "purpose": "Display individual blog posts",
                "props": {"title": "string", "content": "string", "date": "date", "author": "string"},
                "children": ["Comments", "ShareButtons"],
                "styling": "Card layout with typography optimization"
            }
        ],
        "features": ["Responsive design", "Blog post creation and editing"],
        "dependencies": ["react", "typescript"]
    }
    
    # Test component generation
    for component in project_spec["components"]:
        print(f"\n🔧 Testing component generation for: {component['name']}")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a React/TypeScript expert. Generate clean, modern components.

Requirements:
- Use TypeScript with proper types
- Use functional components with hooks
- Include Tailwind CSS classes
- Make components responsive and accessible
- Return ONLY the component code, no explanations or markdown"""),
            ("user", f"""Generate a React component:

Name: {component['name']}
Purpose: {component['purpose']}
Props: {json.dumps(component.get('props', {})).replace('{', '{{').replace('}', '}}')}
Children: {', '.join(component.get('children', []))}
Styling: {component.get('styling', '')}
Project: {project_spec['description']}""")
        ])
        
        try:
            print(f"  Sending request to LLM...")
            response = llm.invoke(prompt.format_messages())
            print(f"  ✅ LLM Response received: {len(response.content)} characters")
            
            # Check if response looks like valid React code
            content = response.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith('```'):
                lines = content.split('\n')
                if len(lines) > 2:
                    content = '\n'.join(lines[1:-1])  # Remove first and last lines
                    content = content.strip()
            
            # Basic validation
            if ("import" in content and ("React" in content or "FC" in content or "useState" in content)) or f"function {component['name']}" in content or f"const {component['name']}" in content:
                print(f"  ✅ Response appears to be valid React code")
                
                # Print first few lines
                lines = content.split('\n')[:10]
                print(f"  📄 First 10 lines:")
                for i, line in enumerate(lines, 1):
                    print(f"    {i:2d}: {line}")
                if len(content.split('\n')) > 10:
                    remaining = len(content.split('\n')) - 10
                    print(f"    ... ({remaining} more lines)")
                    
            else:
                print(f"  ❌ Response doesn't appear to be valid React code")
                print(f"  Raw response: {content[:200]}...")
                return False
                
        except Exception as e:
            print(f"  ❌ Component generation failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    print(f"\n🎉 Component generation step is working correctly!")
    return True

if __name__ == "__main__":
    success = test_component_generation()
    if success:
        print("\n✅ All components generated successfully!")
    else:
        print("\n❌ Component generation step needs fixing") 