#!/usr/bin/env python3
"""
Simple test to isolate LLM issues
"""

import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

def test_basic_llm():
    """Test basic LLM functionality"""
    load_dotenv()
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        return False
    
    print("🧪 Testing Basic LLM Functionality")
    print("="*40)
    
    try:
        llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            anthropic_api_key=api_key,
            temperature=0.1
        )
        
        print("📡 Sending basic request...")
        response = llm.invoke("Say hello")
        
        print(f"✅ LLM response: {response.content}")
        return True
        
    except Exception as e:
        print(f"❌ Basic LLM test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_json_response():
    """Test JSON response with simple prompt"""
    load_dotenv()
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        return False
    
    print("\n🧪 Testing JSON Response")
    print("="*30)
    
    try:
        llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            anthropic_api_key=api_key,
            temperature=0.1
        )
        
        prompt = """You are a helpful assistant. Return ONLY a valid JSON object with this exact structure:
{"message": "Hello World", "status": "success"}

Do not include any other text, just the JSON."""
        
        print("📡 Sending JSON request...")
        response = llm.invoke(prompt)
        
        print(f"📥 Response: {repr(response.content)}")
        
        import json
        try:
            parsed = json.loads(response.content)
            print(f"✅ JSON parsing successful: {parsed}")
            return True
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            print(f"📝 Full response: {response.content}")
            return False
        
    except Exception as e:
        print(f"❌ JSON test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 Simple LLM Test")
    print("="*20)
    
    # Test basic functionality first
    basic_success = test_basic_llm()
    
    if basic_success:
        print("\n✅ Basic LLM test passed")
        # Test JSON response
        json_success = test_json_response()
        
        if json_success:
            print("\n✅ JSON test passed - LLM is working correctly")
        else:
            print("\n❌ JSON test failed - there's an issue with JSON generation")
    else:
        print("\n❌ Basic LLM test failed - there's a fundamental issue") 