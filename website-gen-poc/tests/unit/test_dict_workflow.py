#!/usr/bin/env python3
"""
Test LangGraph with dict state
"""

import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

def dict_node(state: dict):
    """Node that works with dict state"""
    print(f"Dict node called with state: {state}")
    
    # Update state
    state["completed_steps"] = state.get("completed_steps", []) + ["dict_test"]
    state["current_step"] = "dict_complete"
    
    print(f"Updated state: {state}")
    return {"state": state}

def dict_route(state: dict):
    """Routing for dict state"""
    print(f"Dict routing - completed steps: {state.get('completed_steps', [])}")
    if "dict_test" in state.get("completed_steps", []):
        return "end"
    else:
        return "error"

def test_dict_workflow():
    """Test LangGraph with dict state"""
    print("Testing LangGraph with dict state...")
    
    # Create workflow
    workflow = StateGraph(dict)
    workflow.add_node("dict_test", dict_node)
    workflow.set_entry_point("dict_test")
    workflow.add_conditional_edges("dict_test", dict_route, {"end": END, "error": END})
    
    # Compile
    app = workflow.compile()
    
    # Create initial state
    initial_state = {
        "user_request": "test request",
        "current_step": "dict_test",
        "completed_steps": [],
        "errors": []
    }
    
    print(f"Initial state: {initial_state}")
    
    # Invoke
    print("Invoking workflow...")
    result = app.invoke({"state": initial_state})
    print(f"Workflow result: {result}")
    print(f"Result type: {type(result)}")
    
    if result:
        print(f"Result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
        if isinstance(result, dict) and "state" in result:
            final_state = result["state"]
            print(f"Final state: {final_state}")
            print(f"Final completed steps: {final_state.get('completed_steps', [])}")
        else:
            print("No 'state' key in result")
    else:
        print("Result is None")

if __name__ == "__main__":
    load_dotenv()
    test_dict_workflow() 