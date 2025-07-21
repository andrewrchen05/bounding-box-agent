#!/usr/bin/env python3
"""
Simple test to debug LangGraph workflow execution
"""

import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from state import WorkflowState

def simple_node(state: WorkflowState):
    """Simple test node"""
    print(f"Simple node called with state: {state.user_request}")
    state.completed_steps.append("simple_test")
    return {"state": state}

def route_after_simple(state: WorkflowState):
    """Simple routing"""
    print(f"Routing after simple node, completed steps: {state.completed_steps}")
    return "end"

def test_simple_workflow():
    """Test a simple LangGraph workflow"""
    load_dotenv()
    
    # Create a simple workflow
    workflow = StateGraph(WorkflowState)
    workflow.add_node("simple_test", simple_node)
    workflow.set_entry_point("simple_test")
    workflow.add_conditional_edges("simple_test", route_after_simple, {"end": END})
    
    # Compile and run
    app = workflow.compile()
    
    # Create initial state
    initial_state = WorkflowState(user_request="test", current_step="simple_test")
    
    print("Testing simple workflow...")
    config = {"configurable": {"thread_id": "test-workflow"}}
    result = app.invoke({"state": initial_state}, config)
    print(f"Simple workflow result: {result}")
    
    if result and "state" in result:
        final_state = result["state"]
        print(f"Final state completed steps: {final_state.completed_steps}")
        print(f"Final state errors: {final_state.errors}")
    else:
        print("No result or no state in result")

if __name__ == "__main__":
    test_simple_workflow() 