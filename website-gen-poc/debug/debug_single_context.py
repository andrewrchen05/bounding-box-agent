#!/usr/bin/env python3
"""
Debug script for single-context generation

This script helps debug issues with the single-context generator by:
1. Testing the LLM response directly
2. Showing detailed parsing steps
3. Providing fallback options
"""

import os
import json
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate

def test_llm_response():
    """Test the LLM response directly to see what it's returning"""
    load_dotenv()
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        return False
    
    llm = ChatAnthropic(
        model="claude-3-5-sonnet-20241022",
        anthropic_api_key=api_key,
        temperature=0.2,
        max_tokens=8192
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert full-stack web developer who can generate complete, production-ready React/TypeScript projects from user requests.

Your task is to generate a COMPLETE project structure with all necessary files. You must:

1. ANALYZE the user request and determine the project type and requirements
2. DESIGN the architecture and component structure
3. GENERATE all necessary files including:
   - package.json with all dependencies
   - tsconfig.json
   - tailwind.config.js
   - vite.config.ts
   - index.html
   - All React components (.tsx)
   - CSS files if needed
   - README.md with setup instructions

REQUIREMENTS:
- Use React 18+ with TypeScript
- Use Vite as the build tool
- Use Tailwind CSS for styling
- Create responsive, accessible components
- Include proper error handling
- Add meaningful comments
- Use modern React patterns (hooks, functional components)
- Make the project immediately runnable with npm install && npm run dev

CRITICAL: You MUST respond with ONLY valid JSON. Do not include any markdown formatting, explanations, or other text.

OUTPUT FORMAT:
Return ONLY a JSON object with this EXACT structure:
{{
  "project_info": {{
    "name": "project-name",
    "type": "blog|portfolio|ecommerce|dashboard|landing_page|other",
    "description": "Brief description",
    "features": ["feature1", "feature2"]
  }},
  "files": [
    {{
      "path": "package.json",
      "content": "... complete file content ..."
    }},
    {{
      "path": "src/App.tsx",
      "content": "... complete file content ..."
    }}
  ]
}}

IMPORTANT: 
- Respond with ONLY the JSON object, no other text
- Include ALL necessary files for a working project
- Each file content must be complete and ready to use
- Don't use placeholders or comments like "// add more components here"
- Make sure package.json includes all necessary dependencies
- Ensure the project can run immediately after npm install
- Escape any quotes or special characters in file content properly"""),
        ("user", "Create a frontend project for: Create a simple personal blog")
    ])
    
    print("🧪 Testing LLM Response Directly")
    print("="*50)
    
    try:
        print("📡 Sending request to LLM...")
        response = llm.invoke(prompt.format_messages())
        
        print(f"📥 Response received (length: {len(response.content)} chars)")
        print(f"📄 Response type: {type(response.content)}")
        print(f"📄 Response starts with: {repr(response.content[:100])}")
        print(f"📄 Response ends with: {repr(response.content[-100:])}")
        
        print("\n📝 Full Response Content:")
        print("-" * 30)
        print(response.content)
        print("-" * 30)
        
        # Try to parse as JSON
        print("\n🔍 Attempting JSON parsing...")
        try:
            parsed = json.loads(response.content)
            print("✅ JSON parsing successful!")
            print(f"📋 Keys found: {list(parsed.keys())}")
            if "files" in parsed:
                print(f"📄 Number of files: {len(parsed['files'])}")
            return True
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            print(f"❌ Error position: line {e.lineno}, column {e.colno}")
            
            # Show the problematic area
            lines = response.content.split('\n')
            if e.lineno <= len(lines):
                print(f"📝 Problematic line {e.lineno}: {repr(lines[e.lineno-1])}")
            
            return False
            
    except Exception as e:
        print(f"❌ LLM request failed: {str(e)}")
        return False

def test_simple_prompt():
    """Test with a simpler prompt to see if the issue is with complexity"""
    load_dotenv()
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        return False
    
    llm = ChatAnthropic(
        model="claude-3-5-sonnet-20241022",
        anthropic_api_key=api_key,
        temperature=0.1,
        max_tokens=4000
    )
    
    simple_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant. Respond with ONLY a valid JSON object containing a simple message."),
        ("user", "Return a JSON object with this structure: {{'message': 'Hello World', 'status': 'success'}}")
    ])
    
    print("\n🧪 Testing Simple JSON Response")
    print("="*40)
    
    try:
        print("📡 Sending simple request...")
        response = llm.invoke(simple_prompt.format_messages())
        print(f"📥 Response: {repr(response.content)}")
        
        try:
            parsed = json.loads(response.content)
            print(f"✅ Simple JSON parsing successful: {parsed}")
            return True
        except json.JSONDecodeError as e:
            print(f"❌ Simple JSON parsing failed: {e}")
            print(f"📝 Response content: {response.content}")
            return False
            
    except Exception as e:
        print(f"❌ Simple request failed: {str(e)}")
        print(f"📝 Exception type: {type(e)}")
        import traceback
        print(f"📝 Full traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 Single-Context Generator Debug Tool")
    print("="*50)
    
    # Test simple JSON first
    simple_success = test_simple_prompt()
    
    if simple_success:
        print("\n✅ Simple JSON test passed - LLM can return JSON")
        print("\n🔍 Now testing complex project generation...")
        test_llm_response()
    else:
        print("\n❌ Simple JSON test failed - LLM has issues with JSON")
        print("This suggests a fundamental issue with the LLM configuration or prompt") 