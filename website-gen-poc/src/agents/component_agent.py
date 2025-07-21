import json
from typing import Dict, Any, List
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from state import WorkflowState, GeneratedFile, ComponentSpec

class ComponentAgent:
    def __init__(self, api_key: str):
        self.llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            anthropic_api_key=api_key,
            temperature=0.2
        )
        
        self.component_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert React/TypeScript developer. Generate clean, modern React components
            based on the provided specification.
            
            Requirements:
            1. Use TypeScript with proper type definitions
            2. Use functional components with hooks
            3. Include proper imports
            4. Add meaningful prop types and interfaces
            5. Include basic styling classes (Tailwind CSS)
            6. Add comments for complex logic
            7. Make components responsive and accessible
            
            Component Structure:
            - Export a default functional component
            - Define prop interfaces at the top
            - Use descriptive variable names
            - Include error handling where appropriate
            
            Return ONLY the component code, no explanations."""),
            ("user", """Generate a React component with these specifications:
            
            Component Name: {component_name}
            Purpose: {purpose}
            Props: {props}
            Children Components: {children}
            Styling Requirements: {styling_requirements}
            Project Context: {project_context}""")
        ])
    
    def generate_component(self, component_spec: ComponentSpec, project_context: str) -> str:
        """Generate a single React component"""
        try:
            response = self.llm.invoke(
                self.component_prompt.format_messages(
                    component_name=component_spec.name,
                    purpose=component_spec.purpose,
                    props=json.dumps(component_spec.props),
                    children=", ".join(component_spec.children),
                    styling_requirements=component_spec.styling_requirements,
                    project_context=project_context
                )
            )
            
            return response.content
            
        except Exception as e:
            return f"// Error generating component: {str(e)}"
    
    def generate_all_components(self, state: WorkflowState) -> WorkflowState:
        """Generate all required components"""
        try:
            if not state.project_spec or not state.project_spec.components:
                state.errors.append("No component specifications available")
                return state
            
            project_context = f"Project: {state.project_spec.description}, Type: {state.project_spec.type}, Framework: {state.project_spec.styling_framework}"
            
            for component_spec in state.project_spec.components:
                # Generate component code
                component_code = self.generate_component(component_spec, project_context)
                
                # Create file
                file_path = f"src/components/{component_spec.name}.tsx"
                generated_file = GeneratedFile(
                    path=file_path,
                    content=component_code,
                    file_type="tsx"
                )
                
                state.generated_files.append(generated_file)
            
            # Generate App.tsx
            app_code = self.generate_app_component(state)
            app_file = GeneratedFile(
                path="src/App.tsx",
                content=app_code,
                file_type="tsx"
            )
            state.generated_files.append(app_file)
            
            # Generate main.tsx
            main_code = self.generate_main_file()
            main_file = GeneratedFile(
                path="src/main.tsx",
                content=main_code,
                file_type="tsx"
            )
            state.generated_files.append(main_file)
            
            state.completed_steps.append("component_generation")
            state.current_step = "integration"
            
            return state
            
        except Exception as e:
            state.errors.append(f"Component generation failed: {str(e)}")
            return state
    
    def generate_app_component(self, state: WorkflowState) -> str:
        """Generate the main App component"""
        if not state.project_spec:
            return "// Error: No project specification"
        
        components = state.project_spec.components
        component_imports = "\n".join([
            f"import {comp.name} from './components/{comp.name}'"
            for comp in components
        ])
        
        # Basic App structure
        app_code = f'''import React from 'react'
import './App.css'
{component_imports}

function App() {{
  return (
    <div className="App min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold text-center mb-8 text-gray-800">
          {state.project_spec.name.title()}
        </h1>
        {self._generate_component_usage(components)}
      </div>
    </div>
  )
}}

export default App'''
        
        return app_code
    
    def _generate_component_usage(self, components: List[ComponentSpec]) -> str:
        """Generate JSX for using components in App"""
        usage_lines = []
        for comp in components:
            if comp.name in ['Header', 'Navigation', 'Nav']:
                usage_lines.append(f"        <{comp.name} />")
        
        # Add main content components
        for comp in components:
            if comp.name not in ['Header', 'Navigation', 'Nav', 'Footer']:
                usage_lines.append(f"        <{comp.name} />")
        
        # Add footer components
        for comp in components:
            if comp.name in ['Footer']:
                usage_lines.append(f"        <{comp.name} />")
        
        return "\n".join(usage_lines)
    
    def generate_main_file(self) -> str:
        """Generate the main.tsx entry point"""
        return '''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)'''

def component_agent_node(state: WorkflowState, api_key: str = "your-anthropic-api-key") -> Dict[str, Any]:
    """LangGraph node function for component generation"""
    agent = ComponentAgent(api_key=api_key)
    updated_state = agent.generate_all_components(state)
    return {"state": updated_state} 