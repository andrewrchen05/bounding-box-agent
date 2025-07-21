#!/usr/bin/env python3
"""
Debug script to isolate LangGraph workflow issues
"""

import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from state import WorkflowState

def debug_node(state: WorkflowState):
    """Debug node that just prints and returns"""
    print(f"Debug node called with user_request: '{state.user_request}'")
    print(f"Current step: {state.current_step}")
    print(f"Completed steps: {state.completed_steps}")
    print(f"Errors: {state.errors}")
    
    # Add a step
    state.completed_steps.append("debug_test")
    state.current_step = "debug_complete"
    
    print(f"Updated state - completed steps: {state.completed_steps}")
    return {"state": state}

def debug_route(state: WorkflowState):
    """Debug routing"""
    print(f"Debug routing - completed steps: {state.completed_steps}")
    if "debug_test" in state.completed_steps:
        return "end"
    else:
        return "error"

def test_workflow_state():
    """Test WorkflowState object directly"""
    print("Testing WorkflowState object...")
    
    # Create a WorkflowState
    state = WorkflowState(
        user_request="test request",
        current_step="debug_test"
    )
    
    print(f"Created state: {state}")
    print(f"State type: {type(state)}")
    print(f"State dict: {state.dict()}")
    
    return state

def test_simple_workflow():
    """Test a simple LangGraph workflow with WorkflowState"""
    print("\nTesting simple LangGraph workflow...")
    
    # Create workflow
    workflow = StateGraph(WorkflowState)
    workflow.add_node("debug_test", debug_node)
    workflow.set_entry_point("debug_test")
    workflow.add_conditional_edges("debug_test", debug_route, {"end": END, "error": END})
    
    # Compile
    app = workflow.compile()
    
    # Create initial state
    initial_state = WorkflowState(
        user_request="test request",
        current_step="debug_test"
    )
    
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
            print(f"Final completed steps: {final_state.completed_steps}")
        else:
            print("No 'state' key in result")
    else:
        print("Result is None")

if __name__ == "__main__":
    load_dotenv()
    
    # Test WorkflowState
    test_workflow_state()
    
    # Test simple workflow
    test_simple_workflow() 