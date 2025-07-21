import json
import re
import time
from typing import Dict, Any, List, Set
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from state import WorkflowState, GeneratedFile, ComponentSpec
from utils import generate_unique_project_name

class IntegrationAgent:
    def __init__(self, api_key: str):
        self.llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            anthropic_api_key=api_key,
            temperature=0.1
        )
        
        self.integration_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert React/TypeScript integration specialist. Your job is to:
            1. Analyze all components and identify missing imports/dependencies
            2. Fix component interfaces and prop types
            3. Add proper routing and navigation
            4. Ensure components can communicate with each other
            5. Add missing dependencies to package.json
            6. Create proper file structure and imports
            7. Fix JSX syntax errors and broken imports
            
            Return a JSON object with:
            - "package_dependencies": list of npm packages to add
            - "component_fixes": list of component fixes with file paths and updated code
            - "routing_setup": routing configuration if needed
            - "global_types": shared TypeScript interfaces/types
            - "syntax_errors": list of JSX/TypeScript syntax errors found and fixes"""),
            ("user", """Analyze these components and fix integration issues:
            
            Components: {components}
            Project Context: {project_context}
            Current Files: {current_files}""")
        ])
        
        self.fix_component_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are fixing a React component to work with other components.
            Fix imports, prop types, JSX syntax errors, and ensure proper integration.
            Return ONLY the corrected component code."""),
            ("user", """Fix this component to work with the project:
            
            Component Code: {component_code}
            Required Imports: {required_imports}
            Component Dependencies: {dependencies}
            Project Context: {project_context}
            Error Context: {error_context}""")
        ])
    
    def analyze_and_fix_integration(self, state: WorkflowState) -> WorkflowState:
        """Analyze all components and fix integration issues"""
        try:
            if not state.generated_files:
                state.errors.append("No generated files to integrate")
                return state
            
            # Extract component information
            components_info = self._extract_components_info(state.generated_files)
            
            # Get project context
            project_context = ""
            if state.project_spec:
                project_context = f"Project: {state.project_spec.name}, Type: {state.project_spec.type}, Description: {state.project_spec.description}"
            
            # Analyze integration issues
            integration_analysis = self._analyze_integration_issues(components_info, project_context)
            
            # Apply fixes
            state = self._apply_integration_fixes(state, integration_analysis)
            
            # Update package.json with missing dependencies
            state = self._update_package_json(state, integration_analysis.get("package_dependencies", []))
            
            # Run additional error detection and fixes
            state = self._detect_and_fix_common_errors(state)
            
            # Finalize project setup
            state = self._finalize_project_setup(state)
            
            state.completed_steps.append("integration")
            state.current_step = "finalization"
            
            return state
            
        except Exception as e:
            state.errors.append(f"Integration failed: {str(e)}")
            return state
    
    def _detect_and_fix_common_errors(self, state: WorkflowState) -> WorkflowState:
        """Detect and fix common integration errors"""
        for file in state.generated_files:
            # Remove markdown code blocks if present (for all file types)
            file.content = self._remove_markdown_blocks(file.content)
            
            if file.file_type == "tsx":
                # Check for common JSX errors
                file.content = self._fix_jsx_errors(file.content)
                
                # Check for missing imports
                file.content = self._fix_missing_imports(file.content)
                
                # Check for broken component references
                file.content = self._fix_component_references(file.content, state.generated_files)
        
        return state
    
    def _fix_jsx_errors(self, content: str) -> str:
        """Fix common JSX syntax errors"""
        # Fix unclosed JSX tags
        content = self._fix_unclosed_jsx_tags(content)
        
        # Fix mismatched JSX tags
        content = self._fix_mismatched_jsx_tags(content)
        
        # Fix undefined component references
        content = self._fix_undefined_components(content)
        
        return content
    
    def _fix_unclosed_jsx_tags(self, content: str) -> str:
        """Fix unclosed JSX tags"""
        # Common patterns for unclosed tags
        patterns = [
            # Fix Link tags that should be anchor tags
            (r'<Link\s+([^>]*?)>([^<]*?)</a>', r'<a \1>\2</a>'),
            (r'<Link\s+([^>]*?)>([^<]*?)</Link>', r'<a \1>\2</a>'),
            
            # Fix other common unclosed tags
            (r'<(\w+)\s+([^>]*?)>([^<]*?)(?!</\1>)', r'<\1 \2>\3</\1>'),
        ]
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        return content
    
    def _fix_mismatched_jsx_tags(self, content: str) -> str:
        """Fix mismatched JSX opening/closing tags"""
        # Replace Link with anchor tags and fix to attributes
        content = re.sub(r'<Link\s+to="([^"]*)"', r'<a href="#"', content)
        content = re.sub(r'</Link>', r'</a>', content)
        
        # Remove react-router-dom imports
        content = re.sub(r'import\s+\{[^}]*Link[^}]*\}\s+from\s+[\'"][^\'"]*react-router-dom[^\'"]*[\'"];?\n?', '', content)
        
        # Fix specific mismatched tag patterns
        content = re.sub(r'<Link([^>]*)>([^<]*)</a>', r'<a\1>\2</a>', content)
        
        return content
    
    def _fix_undefined_components(self, content: str) -> str:
        """Fix undefined component references"""
        # Check for components that might not be imported
        component_pattern = r'<(\w+)(?:\s+[^>]*)?>'
        components_used = re.findall(component_pattern, content)
        
        # Common React components that should be available
        react_components = {'div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a', 'button', 'input', 'form', 'ul', 'li', 'nav', 'header', 'footer', 'main', 'section', 'article', 'aside'}
        
        # Check for custom components that might need imports
        custom_components = set(components_used) - react_components - {'React', 'Fragment'}
        
        # For now, we'll just ensure basic React import is present
        if 'React' not in content and ('<' in content or '>' in content):
            if 'import React' not in content:
                content = 'import React from \'react\';\n' + content
        
        return content
    
    def _fix_missing_imports(self, content: str) -> str:
        """Fix missing imports"""
        # Add React import if JSX is used but React is not imported
        if ('<' in content and '>' in content) and 'import React' not in content:
            content = 'import React from \'react\';\n' + content
        
        # Add useState import if useState is used
        if 'useState' in content and 'import { useState }' not in content and 'import React, { useState }' not in content:
            if 'import React' in content:
                content = content.replace('import React', 'import React, { useState }')
            else:
                content = 'import React, { useState } from \'react\';\n' + content
        
        return content
    
    def _remove_markdown_blocks(self, content: str) -> str:
        """Remove markdown code blocks from the beginning of files"""
        content = content.strip()
        
        # Remove markdown code blocks if present
        if content.startswith('```'):
            lines = content.split('\n')
            if len(lines) > 2:
                # Remove first line (```typescript or similar)
                lines = lines[1:]
                # Remove last line (```)
                if lines and lines[-1].strip() == '```':
                    lines = lines[:-1]
                content = '\n'.join(lines).strip()
        
        return content
    
    def _fix_component_references(self, content: str, all_files: List[GeneratedFile]) -> str:
        """Fix component references to match available components"""
        # Get list of available component names
        available_components = set()
        for file in all_files:
            if file.file_type == "tsx" and "components" in file.path:
                component_name = file.path.split("/")[-1].replace(".tsx", "")
                available_components.add(component_name)
        
        # Check if components are being used but not imported
        for component in available_components:
            if f'<{component}' in content and f'import {component}' not in content:
                # Add import statement
                import_statement = f"import {component} from './components/{component}';\n"
                
                # Find the best place to insert the import
                lines = content.split('\n')
                insert_index = 0
                
                # Look for existing imports
                for i, line in enumerate(lines):
                    if line.strip().startswith('import '):
                        insert_index = i + 1
                
                # Insert the import
                lines.insert(insert_index, import_statement)
                content = '\n'.join(lines)
        
        return content
    
    def _finalize_project_setup(self, state: WorkflowState) -> WorkflowState:
        """Finalize project setup by creating directory and writing files"""
        import os
        from pathlib import Path
        
        try:
            # Create project directory with unique timestamp
            base_project_name = state.project_spec.name if state.project_spec else "generated-project"
            unique_project_name = generate_unique_project_name(base_project_name)
            output_dir = f"generated_projects/{unique_project_name}"
            state.output_directory = output_dir
            
            # Update the project spec with the unique name
            if state.project_spec:
                state.project_spec.name = unique_project_name
            
            # Create directory structure
            os.makedirs(output_dir, exist_ok=True)
            os.makedirs(f"{output_dir}/src", exist_ok=True)
            os.makedirs(f"{output_dir}/src/components", exist_ok=True)
            os.makedirs(f"{output_dir}/public", exist_ok=True)
            
            # Generate package.json if not exists
            package_json_exists = any(f.path == "package.json" for f in state.generated_files)
            if not package_json_exists:
                package_json = self._generate_package_json(state)
                package_file = GeneratedFile(
                    path="package.json",
                    content=package_json,
                    file_type="json"
                )
                state.generated_files.append(package_file)
            
            # Generate vite.config.ts if not exists
            vite_config_exists = any(f.path == "vite.config.ts" for f in state.generated_files)
            if not vite_config_exists:
                vite_config = self._generate_vite_config()
                vite_file = GeneratedFile(
                    path="vite.config.ts",
                    content=vite_config,
                    file_type="ts"
                )
                state.generated_files.append(vite_file)
            
            # Generate index.html if not exists
            index_html_exists = any(f.path == "index.html" for f in state.generated_files)
            if not index_html_exists:
                index_html = self._generate_index_html(state)
                html_file = GeneratedFile(
                    path="index.html",
                    content=index_html,
                    file_type="html"
                )
                state.generated_files.append(html_file)
            
            # Generate CSS files
            css_files = [
                ("src/index.css", self._generate_index_css()),
                ("src/App.css", self._generate_app_css())
            ]
            
            for css_path, css_content in css_files:
                css_exists = any(f.path == css_path for f in state.generated_files)
                if not css_exists:
                    css_file = GeneratedFile(
                        path=css_path,
                        content=css_content,
                        file_type="css"
                    )
                    state.generated_files.append(css_file)
            
            # Write all files to disk
            for file in state.generated_files:
                file_path = f"{output_dir}/{file.path}"
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(file.content)
            
            # Generate README
            readme_content = self._generate_readme(state)
            readme_path = f"{output_dir}/README.md"
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            
            # Set ready to run
            state.ready_to_run = True
            
            print(f"✅ Project generated successfully in: {output_dir}")
            
        except Exception as e:
            state.errors.append(f"Project finalization failed: {str(e)}")
            print(f"❌ Project finalization failed: {str(e)}")
        
        return state
    
    def _generate_package_json(self, state: WorkflowState) -> str:
        """Generate package.json file"""
        project_name = state.project_spec.name if state.project_spec else "generated-project"
        
        return f'''{{
  "name": "{project_name}",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {{
    "dev": "vite",
    "build": "tsc && vite build",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "preview": "vite preview"
  }},
  "dependencies": {{
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  }},
  "devDependencies": {{
    "@types/react": "^18.2.43",
    "@types/react-dom": "^18.2.17",
    "@typescript-eslint/eslint-plugin": "^6.14.0",
    "@typescript-eslint/parser": "^6.14.0",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.16",
    "eslint": "^8.55.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.5",
    "postcss": "^8.4.32",
    "tailwindcss": "^3.3.6",
    "typescript": "^5.2.2",
    "vite": "^5.0.8"
  }}
}}'''
    
    def _generate_vite_config(self) -> str:
        """Generate vite.config.ts file"""
        return '''import {{ defineConfig }} from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({{
  plugins: [react()],
}})
'''
    
    def _generate_index_html(self, state: WorkflowState) -> str:
        """Generate index.html file"""
        project_name = state.project_spec.name if state.project_spec else "Generated Project"
        
        return f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{project_name}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
'''
    
    def _generate_index_css(self) -> str:
        """Generate index.css file with Tailwind"""
        return '''@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  font-family: Inter, system-ui, Avenir, Helvetica, Arial, sans-serif;
  line-height: 1.5;
  font-weight: 400;

  color-scheme: light dark;
  color: rgba(255, 255, 255, 0.87);
  background-color: #242424;

  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  -webkit-text-size-adjust: 100%;
}

a {
  font-weight: 500;
  color: #646cff;
  text-decoration: inherit;
}
a:hover {
  color: #535bf2;
}

body {
  margin: 0;
  display: flex;
  place-items: center;
  min-width: 320px;
  min-height: 100vh;
}

h1 {
  font-size: 3.2em;
  line-height: 1.1;
}

button {
  border-radius: 8px;
  border: 1px solid transparent;
  padding: 0.6em 1.2em;
  font-size: 1em;
  font-weight: 500;
  font-family: inherit;
  background-color: #1a1a1a;
  cursor: pointer;
  transition: border-color 0.25s;
}
button:hover {
  border-color: #646cff;
}
button:focus,
button:focus-visible {
  outline: 4px auto -webkit-focus-ring-color;
}

@media (prefers-color-scheme: light) {
  :root {
    color: #213547;
    background-color: #ffffff;
  }
  a:hover {
    color: #747bff;
  }
  button {
    background-color: #f9f9f9;
  }
}
'''
    
    def _generate_app_css(self) -> str:
        """Generate App.css file"""
        return '''#root {
  max-width: 1280px;
  margin: 0 auto;
  padding: 2rem;
  text-align: center;
}

.logo {
  height: 6em;
  padding: 1.5em;
  will-change: filter;
  transition: filter 300ms;
}
.logo:hover {
  filter: drop-shadow(0 0 2em #646cffaa);
}
.logo.react:hover {
  filter: drop-shadow(0 0 2em #61dafbaa);
}

@keyframes logo-spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@media (prefers-reduced-motion: no-preference) {
  a:nth-of-type(2) .logo {
    animation: logo-spin infinite 20s linear;
  }
}

.card {
  padding: 2em;
}

.read-the-docs {
  color: #888;
}
'''
    
    def _generate_readme(self, state: WorkflowState) -> str:
        """Generate README.md file"""
        project_name = state.project_spec.name if state.project_spec else "Generated Project"
        description = state.project_spec.description if state.project_spec else "A React TypeScript project"
        
        return f'''# {project_name}

{description}

## Getting Started

This project was generated using an AI-powered frontend generator.

### Prerequisites

- Node.js (version 18 or higher)
- npm or yarn

### Installation

1. Install dependencies:
\`\`\`bash
npm install
\`\`\`

2. Start the development server:
\`\`\`bash
npm run dev
\`\`\`

3. Open your browser and navigate to \`http://localhost:5173\`

### Available Scripts

- \`npm run dev\` - Start development server
- \`npm run build\` - Build for production
- \`npm run preview\` - Preview production build
- \`npm run lint\` - Run ESLint

### Project Structure

\`\`\`
src/
├── components/     # React components
├── App.tsx        # Main App component
├── main.tsx       # Entry point
├── index.css      # Global styles
└── App.css        # App-specific styles
\`\`\`

## Technologies Used

- React 18
- TypeScript
- Vite
- Tailwind CSS
- ESLint

## Generated Components

This project includes the following generated components:

{self._generate_component_list(state)}

## Customization

Feel free to modify the components and add your own functionality!
'''
    
    def _generate_component_list(self, state: WorkflowState) -> str:
        """Generate list of components for README"""
        if not state.project_spec or not state.project_spec.components:
            return "- No components specified"
        
        component_list = []
        for component in state.project_spec.components:
            component_list.append(f"- **{component.name}**: {component.purpose}")
        
        return "\n".join(component_list)
    
    def _extract_components_info(self, files: List[GeneratedFile]) -> List[Dict[str, Any]]:
        """Extract information about all components"""
        components = []
        
        for file in files:
            if file.file_type == "tsx" and "components" in file.path:
                # Extract component name from file path
                component_name = file.path.split("/")[-1].replace(".tsx", "")
                
                # Analyze component content
                imports = self._extract_imports(file.content)
                props = self._extract_props(file.content)
                exports = self._extract_exports(file.content)
                
                components.append({
                    "name": component_name,
                    "path": file.path,
                    "content": file.content,
                    "imports": imports,
                    "props": props,
                    "exports": exports
                })
        
        return components
    
    def _extract_imports(self, content: str) -> List[str]:
        """Extract import statements from component code"""
        import_pattern = r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]'
        imports = re.findall(import_pattern, content)
        return imports
    
    def _extract_props(self, content: str) -> List[str]:
        """Extract prop types from component code"""
        prop_pattern = r'interface\s+(\w+Props)\s*\{'
        props = re.findall(prop_pattern, content)
        return props
    
    def _extract_exports(self, content: str) -> List[str]:
        """Extract export statements from component code"""
        export_pattern = r'export\s+(?:default\s+)?(\w+)'
        exports = re.findall(export_pattern, content)
        return exports
    
    def _analyze_integration_issues(self, components: List[Dict[str, Any]], project_context: str) -> Dict[str, Any]:
        """Analyze components and identify integration issues"""
        try:
            components_json = json.dumps(components, indent=2)
            current_files = [f"{comp['path']}: {len(comp['content'])} chars" for comp in components]
            
            response = self.llm.invoke(
                self.integration_prompt.format_messages(
                    components=components_json,
                    project_context=project_context,
                    current_files=json.dumps(current_files)
                )
            )
            
            # Parse the response as JSON
            try:
                return json.loads(response.content)
            except json.JSONDecodeError:
                # If not valid JSON, create a basic analysis
                return self._create_basic_analysis(components)
                
        except Exception as e:
            return self._create_basic_analysis(components)
    
    def _create_basic_analysis(self, components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a basic integration analysis when LLM fails"""
        package_dependencies = []
        component_fixes = []
        
        # Check for common missing dependencies
        all_imports = set()
        for comp in components:
            all_imports.update(comp['imports'])
        
        if any('react-router' in imp for imp in all_imports):
            package_dependencies.append("react-router-dom")
        
        if any('@heroicons' in imp for imp in all_imports):
            package_dependencies.append("@heroicons/react")
        
        return {
            "package_dependencies": package_dependencies,
            "component_fixes": component_fixes,
            "routing_setup": None,
            "global_types": [],
            "syntax_errors": []
        }
    
    def _apply_integration_fixes(self, state: WorkflowState, analysis: Dict[str, Any]) -> WorkflowState:
        """Apply the integration fixes to the state"""
        # Apply component fixes
        for fix in analysis.get("component_fixes", []):
            file_path = fix.get("file_path")
            updated_code = fix.get("updated_code")
            
            if file_path and updated_code:
                # Find and update the file
                for file in state.generated_files:
                    if file.path == file_path:
                        file.content = updated_code
                        break
        
        # Add global types file if needed
        global_types = analysis.get("global_types", [])
        if global_types:
            types_content = self._generate_types_file(global_types)
            types_file = GeneratedFile(
                path="src/types/index.ts",
                content=types_content,
                file_type="ts"
            )
            state.generated_files.append(types_file)
        
        # Add routing setup if needed
        routing_setup = analysis.get("routing_setup")
        if routing_setup:
            state = self._add_routing_setup(state, routing_setup)
        
        return state
    
    def _generate_types_file(self, types: List[str]) -> str:
        """Generate a TypeScript types file"""
        types_content = "// Global types for the project\n\n"
        for type_def in types:
            types_content += f"{type_def}\n\n"
        return types_content
    
    def _add_routing_setup(self, state: WorkflowState, routing_config: Dict[str, Any]) -> WorkflowState:
        """Add routing setup to the project"""
        # Update App.tsx with routing
        for file in state.generated_files:
            if file.path == "src/App.tsx":
                file.content = self._add_routing_to_app(file.content, routing_config)
                break
        
        return state
    
    def _add_routing_to_app(self, app_content: str, routing_config: Dict[str, Any]) -> str:
        """Add routing to the App component"""
        # Simple routing setup
        routing_imports = """
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
"""
        
        # Replace the basic App structure with routing
        if "function App()" in app_content:
            # Find the return statement and wrap with Router
            app_content = app_content.replace(
                "function App() {",
                "function App() {"
            )
            
            # Add routing imports at the top
            if "import React from 'react'" in app_content:
                app_content = app_content.replace(
                    "import React from 'react'",
                    "import React from 'react'\nimport { BrowserRouter as Router, Routes, Route } from 'react-router-dom'"
                )
            
            # Wrap the return content with Router
            if "<div className=" in app_content:
                app_content = app_content.replace(
                    "<div className=",
                    "<Router>\n    <div className="
                )
                app_content = app_content.replace(
                    "</div>",
                    "</div>\n  </Router>"
                )
        
        return app_content
    
    def _update_package_json(self, state: WorkflowState, dependencies: List[str]) -> WorkflowState:
        """Update package.json with missing dependencies"""
        # Find package.json file
        package_file = None
        for file in state.generated_files:
            if file.path == "package.json":
                package_file = file
                break
        
        if package_file and dependencies:
            try:
                package_data = json.loads(package_file.content)
                
                # Add dependencies
                for dep in dependencies:
                    if dep not in package_data.get("dependencies", {}):
                        if "dependencies" not in package_data:
                            package_data["dependencies"] = {}
                        package_data["dependencies"][dep] = "^6.0.0"  # Default version
                
                package_file.content = json.dumps(package_data, indent=2)
                
            except json.JSONDecodeError:
                state.errors.append("Could not parse package.json")
        
        return state
    
    def fix_component_imports(self, component_code: str, required_imports: List[str], dependencies: List[str]) -> str:
        """Fix imports for a specific component"""
        try:
            response = self.llm.invoke(
                self.fix_component_prompt.format_messages(
                    component_code=component_code,
                    required_imports=json.dumps(required_imports),
                    dependencies=json.dumps(dependencies),
                    project_context="React TypeScript project with Tailwind CSS",
                    error_context="Fix any JSX syntax errors, missing imports, or undefined components"
                )
            )
            
            return response.content
            
        except Exception as e:
            return f"// Error fixing component: {str(e)}\n{component_code}"

def integration_agent_node(state: WorkflowState) -> Dict[str, Any]:
    """LangGraph node function for integration"""
    agent = IntegrationAgent(api_key="your-anthropic-api-key")
    updated_state = agent.analyze_and_fix_integration(state)
    return {"state": updated_state} 