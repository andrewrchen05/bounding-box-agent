import json
from typing import Dict, Any
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from state import WorkflowState, ProjectSpec, ComponentSpec, ProjectType

class RequirementsAgent:
    def __init__(self, api_key: str):
        self.llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            anthropic_api_key=api_key,
            temperature=0.1
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a requirements analysis expert for frontend web applications. 
            Your job is to analyze user requests and convert them into detailed technical specifications.
            
            For any request, determine:
            1. Project type (blog, portfolio, ecommerce, dashboard, landing_page, other)
            2. Required components and their purposes
            3. Key features needed
            4. Styling preferences
            5. Dependencies required
            
            Be specific about component structure and relationships.
            
            Return your analysis as a JSON object matching this structure:
            {{
                "name": "project-name",
                "type": "blog|portfolio|ecommerce|dashboard|landing_page|other",
                "description": "Brief description",
                "components": [
                    {{
                        "name": "ComponentName",
                        "purpose": "What this component does",
                        "props": {{"prop1": "type", "prop2": "type"}},
                        "children": ["ChildComponent1", "ChildComponent2"],
                        "styling_requirements": "Specific styling needs"
                    }}
                ],
                "dependencies": ["react", "typescript", "@types/react"],
                "styling_framework": "tailwind|css-modules|styled-components",
                "features": ["feature1", "feature2"]
            }}"""),
            ("user", "{user_request}")
        ])
    
    def analyze_requirements(self, state: WorkflowState) -> WorkflowState:
        """Analyze user request and generate project specification"""
        try:
            response = self.llm.invoke(
                self.prompt.format_messages(user_request=state.user_request)
            )
            

            
            # Parse the JSON response
            spec_data = json.loads(response.content)
            
            # Convert to ProjectSpec
            components = [
                ComponentSpec(**comp) for comp in spec_data.get("components", [])
            ]
            
            project_spec = ProjectSpec(
                name=spec_data["name"],
                type=ProjectType(spec_data["type"]),
                description=spec_data["description"],
                components=components,
                dependencies=spec_data.get("dependencies", []),
                styling_framework=spec_data.get("styling_framework", "tailwind"),
                features=spec_data.get("features", [])
            )
            
            # Update state
            state.project_spec = project_spec
            state.completed_steps.append("requirements_analysis")
            state.current_step = "architecture_planning"
            
            return state
            
        except Exception as e:
            state.errors.append(f"Requirements analysis failed: {str(e)}")
            return state

def requirements_agent_node(state: WorkflowState, api_key: str = None) -> Dict[str, Any]:
    """LangGraph node function for requirements analysis"""
    import os
    if api_key is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
    agent = RequirementsAgent(api_key=api_key)
    updated_state = agent.analyze_requirements(state)
    return {"state": updated_state} 