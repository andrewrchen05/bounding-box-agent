#!/usr/bin/env python3
"""
Test script for requirements analysis step
"""

import os
import json
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate

def test_requirements_analysis():
    """Test the requirements analysis step"""
    
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
        temperature=0.1
    )
    
    # Test prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a requirements analysis expert. Convert user requests into detailed project specifications.

IMPORTANT: Return ONLY valid JSON. Do not include any explanations, markdown formatting, or code blocks.

Return a JSON object with this exact structure:
{{
    "name": "project-name",
    "type": "blog|portfolio|ecommerce|dashboard|landing_page",
    "description": "Brief description",
    "components": [
        {{
            "name": "ComponentName",
            "purpose": "What this component does",
            "props": {{"prop1": "type"}},
            "children": ["ChildComponent1"],
            "styling": "Styling requirements"
        }}
    ],
    "features": ["feature1", "feature2"],
    "dependencies": ["react", "typescript"]
}}"""),
        ("user", "Analyze this request: Create a personal blog")
    ])
    
    try:
        print("🔍 Testing requirements analysis...")
        print("Input: 'Create a personal blog'")
        
        print("Sending request to LLM...")
        try:
            messages = prompt.format_messages()
            print(f"Formatted messages: {messages}")
            response = llm.invoke(messages)
            print(f"✅ LLM Response received: {len(response.content)} characters")
            print(f"Raw response: {repr(response.content)}")
        except Exception as e:
            print(f"❌ LLM call failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Try to parse JSON
        try:
            project_spec = json.loads(response.content)
            print("✅ JSON parsed successfully")
            
            # Validate structure
            required_fields = ["name", "type", "description", "components"]
            missing_fields = [field for field in required_fields if field not in project_spec]
            
            if missing_fields:
                print(f"❌ Missing required fields: {missing_fields}")
                return False
            
            print("✅ All required fields present")
            
            # Print the result
            print("\n📋 Generated Project Specification:")
            print(f"  Name: {project_spec['name']}")
            print(f"  Type: {project_spec['type']}")
            print(f"  Description: {project_spec['description']}")
            print(f"  Components: {len(project_spec['components'])}")
            
            for i, comp in enumerate(project_spec['components'], 1):
                print(f"    {i}. {comp['name']} - {comp['purpose']}")
            
            print(f"  Features: {project_spec.get('features', [])}")
            print(f"  Dependencies: {project_spec.get('dependencies', [])}")
            
            return True
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            print(f"Raw response: {response.content[:500]}...")
            return False
            
    except Exception as e:
        print(f"❌ Requirements analysis failed: {e}")
        return False

if __name__ == "__main__":
    success = test_requirements_analysis()
    if success:
        print("\n🎉 Requirements analysis step is working correctly!")
    else:
        print("\n❌ Requirements analysis step needs fixing") 