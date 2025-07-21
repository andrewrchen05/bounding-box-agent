import os
from typing import Dict, Any, Literal, TypedDict
from langgraph.graph import StateGraph, END
from state import WorkflowState
from src.agents.requirements_agent import requirements_agent_node
from src.agents.architecture_agent import architecture_agent_node
from src.agents.component_agent import component_agent_node
from src.agents.integration_agent import integration_agent_node

# TypedDict for LangGraph state (required for compatibility)
class LangGraphState(TypedDict):
    user_request: str
    current_step: str
    completed_steps: list
    errors: list
    generated_files: list
    ready_to_run: bool
    output_directory: str
    project_spec: dict
    architecture_plan: dict

class FrontendGeneratorWorkflow:
    def __init__(self, anthropic_api_key: str):
        if not anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required")
        self.api_key = anthropic_api_key
        os.environ["ANTHROPIC_API_KEY"] = anthropic_api_key
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow with routing logic"""
        
        # Create the graph with TypedDict state (for LangGraph compatibility)
        workflow = StateGraph(LangGraphState)
        
        # Add nodes for each agent
        workflow.add_node("requirements_analysis", self._requirements_node)
        workflow.add_node("architecture_planning", self._architecture_node)
        workflow.add_node("component_generation", self._component_node)
        workflow.add_node("integration", self._integration_node)
        workflow.add_node("error_handler", self._error_handler_node)
        
        # Set entry point
        workflow.set_entry_point("requirements_analysis")
        
        # Add conditional edges with routing logic
        workflow.add_conditional_edges(
            "requirements_analysis",
            self._route_after_requirements,
            {
                "architecture_planning": "architecture_planning",
                "error": "error_handler",
                "end": END
            }
        )
        
        workflow.add_conditional_edges(
            "architecture_planning",
            self._route_after_architecture,
            {
                "component_generation": "component_generation",
                "error": "error_handler",
                "end": END
            }
        )
        
        workflow.add_conditional_edges(
            "component_generation",
            self._route_after_components,
            {
                "integration": "integration",
                "error": "error_handler",
                "end": END
            }
        )
        
        workflow.add_conditional_edges(
            "integration",
            self._route_after_integration,
            {
                "end": END,
                "error": "error_handler"
            }
        )
        
        workflow.add_edge("error_handler", END)
        
        return workflow
    
    def _dict_to_pydantic(self, state_dict: Dict[str, Any]) -> WorkflowState:
        """Convert dict state to Pydantic WorkflowState"""
        try:
            return WorkflowState(**state_dict)
        except Exception as e:
            print(f"Error converting dict to Pydantic: {e}")
            # Return a minimal valid state
            return WorkflowState(
                user_request=state_dict.get("user_request", ""),
                errors=[f"State conversion error: {str(e)}"]
            )
    
    def _pydantic_to_dict(self, state: WorkflowState) -> Dict[str, Any]:
        """Convert Pydantic WorkflowState to dict"""
        return state.model_dump()
    
    def _requirements_node(self, state_dict: LangGraphState) -> LangGraphState:
        """Wrapper for requirements analysis node"""
        from src.agents.requirements_agent import RequirementsAgent
        
        # Convert to Pydantic for agent
        state = self._dict_to_pydantic(state_dict)
        
        agent = RequirementsAgent(self.api_key)
        updated_state = agent.analyze_requirements(state)
        
        # Convert back to dict
        return self._pydantic_to_dict(updated_state)
    
    def _architecture_node(self, state_dict: LangGraphState) -> LangGraphState:
        """Wrapper for architecture planning node"""
        from src.agents.architecture_agent import ArchitectureAgent
        
        # Convert to Pydantic for agent
        state = self._dict_to_pydantic(state_dict)
        
        agent = ArchitectureAgent(self.api_key)
        updated_state = agent.plan_architecture(state)
        
        # Convert back to dict
        return self._pydantic_to_dict(updated_state)
    
    def _component_node(self, state_dict: LangGraphState) -> LangGraphState:
        """Wrapper for component generation node"""
        from src.agents.component_agent import ComponentAgent
        
        # Convert to Pydantic for agent
        state = self._dict_to_pydantic(state_dict)
        
        agent = ComponentAgent(self.api_key)
        updated_state = agent.generate_all_components(state)
        
        # Convert back to dict
        return self._pydantic_to_dict(updated_state)
    
    def _integration_node(self, state_dict: LangGraphState) -> LangGraphState:
        """Wrapper for integration node"""
        from src.agents.integration_agent import IntegrationAgent
        
        # Convert to Pydantic for agent
        state = self._dict_to_pydantic(state_dict)
        
        agent = IntegrationAgent(self.api_key)
        updated_state = agent.analyze_and_fix_integration(state)
        
        # Convert back to dict
        return self._pydantic_to_dict(updated_state)
    
    def _error_handler_node(self, state_dict: LangGraphState) -> LangGraphState:
        """Handle errors in the workflow"""
        # Convert to Pydantic for processing
        state = self._dict_to_pydantic(state_dict)
        
        print(f"Workflow encountered errors: {state.errors}")
        state.current_step = "error"
        
        # Convert back to dict
        return self._pydantic_to_dict(state)
    
    def _route_after_requirements(self, state_dict: LangGraphState) -> Literal["architecture_planning", "error", "end"]:
        """Routing logic after requirements analysis"""
        # Convert to Pydantic for checking
        state = self._dict_to_pydantic(state_dict)
        
        if state.errors:
            return "error"
        if not state.project_spec:
            return "error"
        return "architecture_planning"
    
    def _route_after_architecture(self, state_dict: LangGraphState) -> Literal["component_generation", "error", "end"]:
        """Routing logic after architecture planning"""
        # Convert to Pydantic for checking
        state = self._dict_to_pydantic(state_dict)
        
        if state.errors:
            return "error"
        if not state.architecture_plan:
            return "error"
        return "component_generation"
    
    def _route_after_components(self, state_dict: LangGraphState) -> Literal["integration", "error", "end"]:
        """Routing logic after component generation"""
        # Convert to Pydantic for checking
        state = self._dict_to_pydantic(state_dict)
        
        if state.errors:
            return "error"
        if not state.generated_files:
            return "error"
        return "integration"
    
    def _route_after_integration(self, state_dict: LangGraphState) -> Literal["end", "error"]:
        """Routing logic after integration"""
        # Convert to Pydantic for checking
        state = self._dict_to_pydantic(state_dict)
        
        if state.errors:
            return "error"
        if not state.ready_to_run:
            return "error"
        return "end"
    
    def generate_frontend(self, user_request: str) -> WorkflowState:
        """Main method to generate a frontend from user request"""
        
        # Initialize state as Pydantic model first
        initial_state = WorkflowState(
            user_request=user_request,
            current_step="requirements_analysis"
        )
        
        # Convert to dict for LangGraph
        initial_state_dict = self._pydantic_to_dict(initial_state)
        
        # Compile workflow
        app = self.workflow.compile()
        
        try:
            print("Starting workflow execution...")
            # Execute the workflow
            result = app.invoke(initial_state_dict)
            print(f"Workflow execution result type: {type(result)}")
            
            if result is None:
                print("Workflow execution returned None")
                return WorkflowState(
                    user_request=user_request,
                    errors=["Workflow execution returned None"]
                )
            
            # Convert back to Pydantic
            final_state = self._dict_to_pydantic(result)
            
            # Print summary
            self._print_summary(final_state)
            
            return final_state
            
        except Exception as e:
            print(f"Workflow execution failed: {str(e)}")
            return WorkflowState(
                user_request=user_request,
                errors=[f"Workflow execution failed: {str(e)}"]
            )
    
    def _print_summary(self, state: WorkflowState):
        """Print a summary of the generation process"""
        print("\n" + "="*50)
        print("FRONTEND GENERATION SUMMARY")
        print("="*50)
        
        if state.project_spec:
            print(f"Project: {state.project_spec.name}")
            print(f"Type: {state.project_spec.type}")
            print(f"Description: {state.project_spec.description}")
            print(f"Components: {len(state.project_spec.components)}")
        
        print(f"Generated Files: {len(state.generated_files)}")
        print(f"Output Directory: {state.output_directory}")
        print(f"Completed Steps: {', '.join(state.completed_steps)}")
        
        if state.errors:
            print(f"Errors: {len(state.errors)}")
            for error in state.errors:
                print(f"  - {error}")
        
        if state.ready_to_run:
            print("\n✅ Project is ready to run!")
            print(f"To start the development server:")
            print(f"  cd {state.output_directory}")
            print(f"  npm install")
            print(f"  npm run dev")
        else:
            print("\n❌ Project generation failed or incomplete")
        
        print("="*50)

# Convenience function for easy usage
def generate_frontend_project(user_request: str, anthropic_api_key: str) -> WorkflowState:
    """Generate a frontend project from a user request"""
    workflow = FrontendGeneratorWorkflow(anthropic_api_key)
    return workflow.generate_frontend(user_request) 