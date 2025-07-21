import os
import json
import time
from typing import Dict, Any, List
from pathlib import Path
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from state import WorkflowState, GeneratedFile, ProjectSpec, ComponentSpec, ProjectType
from utils import generate_unique_project_name

class SingleContextGenerator:
    def __init__(self, api_key: str):
        self.llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            anthropic_api_key=api_key,
            temperature=0.2,
            max_tokens=8192
        )
        
        # Create a simple prompt without template to avoid formatting issues
        self.system_prompt = """You are an expert full-stack web developer who can generate complete, production-ready React/TypeScript projects from user requests.

Your task is to generate a COMPLETE project structure with all necessary files. You must:

1. ANALYZE the user request and determine the project type and requirements
2. DESIGN the architecture and component structure
3. GENERATE all necessary files including:
   - package.json with all dependencies
   - tsconfig.json
   - tailwind.config.js
   - vite.config.ts
   - index.html
   - All React components (.tsx)
   - CSS files if needed
   - README.md with setup instructions

REQUIREMENTS:
- Use React 18+ with TypeScript
- Use Vite as the build tool
- Use Tailwind CSS for styling
- Create responsive, accessible components
- Include proper error handling
- Add meaningful comments
- Use modern React patterns (hooks, functional components)
- Make the project immediately runnable with npm install && npm run dev

CRITICAL: You MUST respond with ONLY valid JSON. Do not include any markdown formatting, explanations, or other text.

OUTPUT FORMAT:
Return ONLY a JSON object with this EXACT structure:
{{
  "project_info": {{
    "name": "project-name",
    "type": "blog|portfolio|ecommerce|dashboard|landing_page|other",
    "description": "Brief description",
    "features": ["feature1", "feature2"]
  }},
  "files": [
    {{
      "path": "package.json",
      "content": "... complete file content ..."
    }},
    {{
      "path": "src/App.tsx",
      "content": "... complete file content ..."
    }}
  ]
}}

IMPORTANT: 
- Respond with ONLY the JSON object, no other text
- Include ALL necessary files for a working project
- Each file content must be complete and ready to use
- Don't use placeholders or comments like "// add more components here"
- Make sure package.json includes all necessary dependencies
- Ensure the project can run immediately after npm install
- Escape any quotes or special characters in file content properly"""
    
    def generate_project(self, user_request: str) -> WorkflowState:
        """Generate a complete frontend project in a single context"""
        
        state = WorkflowState(
            user_request=user_request,
            current_step="single_context_generation"
        )
        
        try:
            print("🎯 Generating complete project in single context...")
            
            # Generate the entire project
            print("📡 Sending request to LLM...")
            
            # Create the full prompt
            full_prompt = f"{self.system_prompt}\n\nCreate a frontend project for: {user_request}"
            
            response = self.llm.invoke(full_prompt)
            
            print(f"📥 Received response from LLM (length: {len(response.content)} chars)")
            print(f"📄 Response preview (first 200 chars): {response.content[:200]}...")
            
            # Parse the JSON response
            print("🔍 Attempting to parse JSON response...")
            try:
                project_data = json.loads(response.content)
                print("✅ Successfully parsed JSON response")
            except json.JSONDecodeError as e:
                print(f"❌ Initial JSON parsing failed: {e}")
                print("🔍 Attempting to extract JSON from markdown...")
                
                # Try to extract JSON from response if it's wrapped in markdown
                content = response.content.strip()
                print(f"📝 Content starts with: {content[:50]}...")
                print(f"📝 Content ends with: {content[-50:]}...")
                
                # Try multiple extraction patterns
                extracted_content = None
                
                # Pattern 1: ```json ... ```
                if "```json" in content:
                    print("🔍 Found ```json pattern")
                    start = content.find("```json") + 7
                    end = content.find("```", start)
                    if end != -1:
                        extracted_content = content[start:end].strip()
                        print(f"📝 Extracted content (first 100 chars): {extracted_content[:100]}...")
                
                # Pattern 2: ``` ... ``` (without json specifier)
                elif "```" in content and extracted_content is None:
                    print("🔍 Found ``` pattern")
                    start = content.find("```") + 3
                    end = content.find("```", start)
                    if end != -1:
                        extracted_content = content[start:end].strip()
                        print(f"📝 Extracted content (first 100 chars): {extracted_content[:100]}...")
                
                # Pattern 3: Look for JSON object boundaries
                elif extracted_content is None:
                    print("🔍 Looking for JSON object boundaries...")
                    # Find first { and last }
                    first_brace = content.find("{")
                    last_brace = content.rfind("}")
                    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                        extracted_content = content[first_brace:last_brace + 1]
                        print(f"📝 Extracted content (first 100 chars): {extracted_content[:100]}...")
                
                if extracted_content:
                    try:
                        project_data = json.loads(extracted_content)
                        print("✅ Successfully parsed extracted JSON")
                    except json.JSONDecodeError as e2:
                        print(f"❌ Extracted content JSON parsing failed: {e2}")
                        print(f"📝 Full extracted content:")
                        print(extracted_content)
                        raise Exception(f"Failed to parse JSON response after extraction: {e2}")
                else:
                    print("❌ Could not extract JSON content")
                    print(f"📝 Full response content:")
                    print(response.content)
                    raise Exception(f"Failed to parse JSON response: {e}")
            
            # Extract project info
            print("📋 Extracting project information...")
            project_info = project_data.get("project_info", {})
            files = project_data.get("files", [])
            
            print(f"📁 Project info: {project_info}")
            print(f"📄 Number of files: {len(files)}")
            
            if not files:
                print("❌ No files found in response")
                print(f"📝 Available keys in response: {list(project_data.keys())}")
                raise Exception("No files generated in response")
            
            # Create project spec
            state.project_spec = ProjectSpec(
                name=project_info.get("name", "generated-project"),
                type=ProjectType(project_info.get("type", "other")),
                description=project_info.get("description", "Generated project"),
                features=project_info.get("features", []),
                styling_framework="tailwind"
            )
            
            # Convert files to GeneratedFile objects
            print("📝 Processing generated files...")
            for i, file_info in enumerate(files):
                print(f"  📄 Processing file {i+1}/{len(files)}: {file_info.get('path', 'unknown')}")
                
                if not isinstance(file_info, dict):
                    print(f"    ❌ File info is not a dict: {type(file_info)}")
                    continue
                    
                if "path" not in file_info or "content" not in file_info:
                    print(f"    ❌ Missing path or content: {list(file_info.keys())}")
                    continue
                    
                generated_file = GeneratedFile(
                    path=file_info["path"],
                    content=file_info["content"],
                    file_type=self._get_file_type(file_info["path"])
                )
                state.generated_files.append(generated_file)
                print(f"    ✅ Added file: {file_info['path']} ({len(file_info['content'])} chars)")
            
            # Set up output directory with unique timestamp
            base_project_name = project_info.get("name", "generated-project")
            unique_project_name = generate_unique_project_name(base_project_name)
            state.output_directory = f"generated_projects/{unique_project_name}"
            print(f"📁 Output directory: {state.output_directory}")
            
            # Update the project spec with the unique name
            state.project_spec.name = unique_project_name
            
            # Write files to disk
            print("💾 Writing files to disk...")
            self._write_files_to_disk(state)
            
            # Update state
            state.completed_steps = ["single_context_generation", "file_generation", "project_setup"]
            state.current_step = "completed"
            state.ready_to_run = True
            
            print(f"✅ Generated {len(state.generated_files)} files successfully!")
            
            return state
            
        except Exception as e:
            error_msg = f"Single context generation failed: {str(e)}"
            print(f"❌ {error_msg}")
            state.errors.append(error_msg)
            
            # Try to create a minimal fallback project
            print("🔄 Attempting to create minimal fallback project...")
            try:
                fallback_state = self._create_fallback_project(user_request)
                if fallback_state:
                    print("✅ Fallback project created successfully")
                    return fallback_state
            except Exception as fallback_error:
                print(f"❌ Fallback project creation also failed: {fallback_error}")
            
            return state
    
    def _get_file_type(self, file_path: str) -> str:
        """Determine file type from path"""
        ext = Path(file_path).suffix.lower()
        type_map = {
            ".tsx": "tsx",
            ".ts": "ts",
            ".js": "js",
            ".jsx": "jsx",
            ".json": "json",
            ".html": "html",
            ".css": "css",
            ".md": "markdown",
            ".config.js": "config",
            ".config.ts": "config"
        }
        return type_map.get(ext, "text")
    
    def _write_files_to_disk(self, state: WorkflowState):
        """Write generated files to the output directory"""
        output_path = Path(state.output_directory)
        
        # Create output directory
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Write each file
        for generated_file in state.generated_files:
            file_path = output_path / generated_file.path
            
            # Create parent directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(generated_file.content)
        
        print(f"📁 Files written to: {output_path.absolute()}")
    
    def _create_fallback_project(self, user_request: str) -> WorkflowState:
        """Create a minimal fallback project when main generation fails"""
        print("🔧 Creating minimal fallback project...")
        
        # Create basic project structure with unique timestamp
        project_name = generate_unique_project_name("fallback-project")
        state = WorkflowState(
            user_request=user_request,
            current_step="fallback_generation",
            output_directory=f"generated_projects/{project_name}"
        )
        
        # Create project spec
        state.project_spec = ProjectSpec(
            name=project_name,
            type=ProjectType.OTHER,
            description=f"Fallback project for: {user_request}",
            features=["basic", "fallback"],
            styling_framework="tailwind"
        )
        
        # Create minimal files
        files = [
            {
                "path": "package.json",
                "content": '''{
  "name": "fallback-project",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
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
  }
}'''
            },
            {
                "path": "index.html",
                "content": '''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Fallback Project</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>'''
            },
            {
                "path": "src/main.tsx",
                "content": '''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)'''
            },
            {
                "path": "src/App.tsx",
                "content": '''import { useState } from 'react'
import './App.css'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-800 mb-4">
          Fallback Project
        </h1>
        <p className="text-gray-600 mb-8">
          This is a minimal fallback project. The main generation failed.
        </p>
        <div className="bg-white p-8 rounded-lg shadow-md">
          <p className="text-gray-700 mb-4">
            Original request: {user_request}
          </p>
          <button
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
            onClick={() => setCount((count) => count + 1)}
          >
            Count is {count}
          </button>
        </div>
      </div>
    </div>
  )
}

export default App'''
            },
            {
                "path": "src/App.css",
                "content": '''/* App-specific styles */
@tailwind base;
@tailwind components;
@tailwind utilities;'''
            },
            {
                "path": "src/index.css",
                "content": '''@tailwind base;
@tailwind components;
@tailwind utilities;'''
            },
            {
                "path": "vite.config.ts",
                "content": '''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
})'''
            },
            {
                "path": "tsconfig.json",
                "content": '''{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,

    /* Bundler mode */
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",

    /* Linting */
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}'''
            },
            {
                "path": "tsconfig.node.json",
                "content": '''{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}'''
            },
            {
                "path": "tailwind.config.js",
                "content": '''/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}'''
            },
            {
                "path": "postcss.config.js",
                "content": '''export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}'''
            },
            {
                "path": "README.md",
                "content": f'''# Fallback Project

This is a minimal fallback project that was created because the main generation failed.

## Original Request
{user_request}

## Setup
\`\`\`bash
npm install
npm run dev
\`\`\`

## What happened?
The AI generation failed to produce a proper JSON response. This fallback project provides a basic working React/TypeScript setup that you can build upon.

## Next Steps
1. Run the project to verify it works
2. Modify the components in \`src/\` to match your requirements
3. Add additional features as needed
'''
            }
        ]
        
        # Convert to GeneratedFile objects
        for file_info in files:
            generated_file = GeneratedFile(
                path=file_info["path"],
                content=file_info["content"],
                file_type=self._get_file_type(file_info["path"])
            )
            state.generated_files.append(generated_file)
        
        # Write files to disk
        self._write_files_to_disk(state)
        
        # Update state
        state.completed_steps = ["fallback_generation"]
        state.current_step = "completed"
        state.ready_to_run = True
        
        return state

def generate_frontend_project_single_context(user_request: str, anthropic_api_key: str) -> WorkflowState:
    """Generate a frontend project in a single context"""
    generator = SingleContextGenerator(anthropic_api_key)
    return generator.generate_project(user_request) 