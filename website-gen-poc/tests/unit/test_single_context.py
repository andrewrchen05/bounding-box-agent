#!/usr/bin/env python3
"""
Test script for single-context generation mode

This script demonstrates both generation modes:
1. Multi-agent workflow (default)
2. Single-context generation (new)
"""

import os
import time
from dotenv import load_dotenv
from src.workflows.workflow_pydantic_compatible import generate_frontend_project
from src.generators.single_context_generator import generate_frontend_project_single_context

def test_single_context():
    """Test the single-context generation mode"""
    load_dotenv()
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        return False
    
    user_request = "Create a simple portfolio website with a hero section, about section, and contact form"
    
    print("🧪 Testing Single-Context Generation")
    print("="*50)
    print(f"Request: {user_request}")
    print("-"*50)
    
    start_time = time.time()
    
    try:
        # Test single-context generation
        state = generate_frontend_project_single_context(user_request, api_key)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n⏱️  Generation completed in {duration:.2f} seconds")
        print(f"📁 Output directory: {state.output_directory}")
        print(f"📄 Files generated: {len(state.generated_files)}")
        print(f"✅ Ready to run: {state.ready_to_run}")
        
        if state.errors:
            print(f"❌ Errors: {len(state.errors)}")
            for error in state.errors:
                print(f"   - {error}")
        
        # List generated files
        print("\n📋 Generated Files:")
        for file in state.generated_files:
            print(f"   - {file.path} ({file.file_type})")
        
        return state.ready_to_run and not state.errors
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def compare_modes():
    """Compare both generation modes"""
    load_dotenv()
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        return
    
    user_request = "Create a simple landing page for a tech startup"
    
    print("🔄 Comparing Generation Modes")
    print("="*60)
    print(f"Request: {user_request}")
    print("="*60)
    
    # Test single-context mode
    print("\n1️⃣ Single-Context Mode:")
    print("-"*30)
    
    start_time = time.time()
    try:
        single_state = generate_frontend_project_single_context(user_request, api_key)
        single_duration = time.time() - start_time
        
        print(f"✅ Time: {single_duration:.2f}s")
        print(f"📄 Files: {len(single_state.generated_files)}")
        print(f"🎯 Success: {single_state.ready_to_run and not single_state.errors}")
        
    except Exception as e:
        print(f"❌ Failed: {str(e)}")
        single_duration = None
        single_state = None
    
    # Test multi-agent mode
    print("\n2️⃣ Multi-Agent Mode:")
    print("-"*30)
    
    start_time = time.time()
    try:
        multi_state = generate_frontend_project(user_request, api_key)
        multi_duration = time.time() - start_time
        
        print(f"✅ Time: {multi_duration:.2f}s")
        print(f"📄 Files: {len(multi_state.generated_files)}")
        print(f"🎯 Success: {multi_state.ready_to_run and not multi_state.errors}")
        
    except Exception as e:
        print(f"❌ Failed: {str(e)}")
        multi_duration = None
        multi_state = None
    
    # Comparison summary
    print("\n📊 Summary:")
    print("-"*20)
    
    if single_duration and multi_duration:
        speedup = multi_duration / single_duration
        print(f"Single-context is {speedup:.1f}x {'faster' if speedup > 1 else 'slower'}")
    
    print("\nAdvantages:")
    print("Single-context: Faster, more coherent, single LLM call")
    print("Multi-agent: More structured, better error handling, modular")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--compare":
        compare_modes()
    else:
        success = test_single_context()
        if success:
            print("\n🎉 Single-context generation test passed!")
        else:
            print("\n💥 Single-context generation test failed!")
            sys.exit(1) 