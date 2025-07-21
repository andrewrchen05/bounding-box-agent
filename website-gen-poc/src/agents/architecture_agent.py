import json
from typing import Dict, Any
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from state import WorkflowState

class ArchitectureAgent:
    def __init__(self, api_key: str):
        self.llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            anthropic_api_key=api_key,
            temperature=0.1
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a frontend architecture expert. Given a project specification,
            design the complete project structure, file organization, and build configuration.
            
            Consider:
            1. Folder structure (src/, components/, pages/, styles/, etc.)
            2. Build tools (Vite, Webpack, etc.)
            3. Package.json configuration
            4. TypeScript configuration
            5. Routing structure
            6. Component hierarchy and relationships
            
            Return ONLY a valid JSON object with this exact structure. Do not include any explanations or markdown formatting:
            {{
                "project_structure": {{
                    "src/": {{
                        "components/": {{}},
                        "pages/": {{}},
                        "styles/": {{}},
                        "types/": {{}},
                        "utils/": {{}}
                    }},
                    "public/": {{}}
                }},
                "build_tool": "vite",
                "package_dependencies": {{
                    "dependencies": {{
                        "react": "^18.0.0",
                        "react-dom": "^18.0.0"
                    }},
                    "devDependencies": {{
                        "typescript": "^5.0.0",
                        "vite": "^4.0.0",
                        "@vitejs/plugin-react": "^3.0.0"
                    }}
                }},
                "routing_structure": [
                    {{
                        "path": "/",
                        "component": "HomePage",
                        "title": "Home"
                    }}
                ],
                "component_hierarchy": {{
                    "App": ["Router", "Layout"],
                    "Layout": ["Header", "Footer"],
                    "HomePage": ["Hero", "BlogList"]
                }}
            }}"""),
            ("user", "Project Spec: {project_spec}")
        ])
    
    def plan_architecture(self, state: WorkflowState) -> WorkflowState:
        """Generate architecture plan from project specification"""
        try:
            if not state.project_spec:
                state.errors.append("No project specification available for architecture planning")
                return state
            
            # Convert project spec to string for LLM
            spec_str = json.dumps(state.project_spec.model_dump(), indent=2)
            
            response = self.llm.invoke(
                self.prompt.format_messages(project_spec=spec_str)
            )
            
            # Parse architecture plan with better error handling
            try:
                # Try to extract JSON from the response
                content = response.content.strip()
                
                # Find JSON block if it's wrapped in markdown
                if "```json" in content:
                    start = content.find("```json") + 7
                    end = content.find("```", start)
                    if end != -1:
                        content = content[start:end].strip()
                elif "```" in content:
                    start = content.find("```") + 3
                    end = content.find("```", start)
                    if end != -1:
                        content = content[start:end].strip()
                
                architecture_plan = json.loads(content)
            except json.JSONDecodeError as json_error:
                print(f"JSON parsing error: {json_error}")
                print(f"Raw response content: {response.content[:500]}...")
                
                # Create a fallback architecture plan
                architecture_plan = {
                    "project_structure": {
                        "src/": {
                            "components/": {},
                            "pages/": {},
                            "styles/": {},
                            "types/": {},
                            "utils/": {}
                        },
                        "public/": {}
                    },
                    "build_tool": "vite",
                    "package_dependencies": {
                        "dependencies": {
                            "react": "^18.0.0",
                            "react-dom": "^18.0.0"
                        },
                        "devDependencies": {
                            "typescript": "^5.0.0",
                            "vite": "^4.0.0",
                            "@vitejs/plugin-react": "^3.0.0"
                        }
                    },
                    "routing_structure": [
                        {
                            "path": "/",
                            "component": "HomePage",
                            "title": "Home"
                        }
                    ],
                    "component_hierarchy": {
                        "App": ["Router", "Layout"],
                        "Layout": ["Header", "Footer"],
                        "HomePage": ["Hero", "BlogList"]
                    }
                }
            
            # Update state
            state.architecture_plan = architecture_plan
            state.project_structure = architecture_plan.get("project_structure", {})
            state.completed_steps.append("architecture_planning")
            state.current_step = "component_generation"
            
            return state
            
        except Exception as e:
            state.errors.append(f"Architecture planning failed: {str(e)}")
            return state

def architecture_agent_node(state: WorkflowState) -> Dict[str, Any]:
    """LangGraph node function for architecture planning"""
    agent = ArchitectureAgent(api_key="your-anthropic-api-key")
    updated_state = agent.plan_architecture(state)
    return {"state": updated_state} 