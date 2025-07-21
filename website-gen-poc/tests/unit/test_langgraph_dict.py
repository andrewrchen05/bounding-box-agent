import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

# Load environment variables
load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY")

def simple_node(state_dict):
    """A simple test node"""
    print(f"Simple node called with: {type(state_dict)}")
    print(f"State dict keys: {state_dict.keys() if isinstance(state_dict, dict) else 'Not a dict'}")
    
    if "state" in state_dict:
        state = state_dict["state"]
    else:
        state = state_dict
    
    print(f"Extracted state type: {type(state)}")
    print(f"State user_request: {state.get('user_request', 'Not found')}")
    
    # Just return the state as-is
    return {"state": state}

def route_function(state_dict):
    """Simple routing function"""
    print(f"Route function called with: {type(state_dict)}")
    return "end"

def test_langgraph_dict():
    """Test basic LangGraph functionality with plain dict"""
    print("Testing LangGraph with plain dict...")
    
    # Create a simple workflow with dict state
    workflow = StateGraph(dict)
    workflow.add_node("simple", simple_node)
    workflow.set_entry_point("simple")
    workflow.add_conditional_edges("simple", route_function, {"end": END})
    
    # Compile
    app = workflow.compile()
    
    # Create initial state as dict
    initial_state = {
        "user_request": "Test request",
        "current_step": "simple"
    }
    
    print(f"Initial state type: {type(initial_state)}")
    print(f"Initial state user_request: {initial_state['user_request']}")
    
    try:
        # Execute
        print("Executing workflow...")
        result = app.invoke({"state": initial_state})
        print(f"Result type: {type(result)}")
        print(f"Result: {result}")
        
        if result is None:
            print("❌ LangGraph returned None")
            return False
        
        final_state = result.get("state")
        if final_state:
            print(f"✅ Final state user_request: {final_state.get('user_request', 'Not found')}")
            return True
        else:
            print("❌ No state in result")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False

if __name__ == "__main__":
    if not api_key:
        print("❌ No API key found")
    else:
        print(f"✅ API key found: {api_key[:10]}...")
        success = test_langgraph_dict()
        print(f"Test {'passed' if success else 'failed'}") 